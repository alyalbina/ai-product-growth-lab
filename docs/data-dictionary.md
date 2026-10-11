# Data dictionary

All generated records are synthetic. Times are UTC represented as timezone-naive ISO strings `YYYY-MM-DD HH:MM:SS` for SQLite compatibility. `user_days.date` is `YYYY-MM-DD`. IDs are integer primary keys, except human-readable session IDs. Binary fields are integers 0/1. Missing `cancelled_at` means not cancelled by the observation cutoff, not lifelong retention.

| Table | Grain and key | Fields and interpretation |
|---|---|---|
| `users` | One randomized registrant; `user_id` | `signup_date`, `acquisition_channel` (organic, paid_search, referral, social), `user_segment` (professional, explorer, casual), `country` (AE, US, GB, DE, IN), `experiment_group` (control/treatment), `observed_days` (age-day count at shared cutoff). |
| `experiment_assignments` | One user; `user_id` FK and PK | `variant` equals users' group; `assigned_at` equals signup. Includes every randomized user, not only visitors. |
| `events` | One event; `event_id` | `user_id` FK, `event_timestamp`, `event_type`, optional `session_id`. Automatic grants and billing can have null sessions. |
| `token_transactions` | One credit-lot movement; `transaction_id` | `user_id`, `timestamp`, `transaction_type` (grant/debit/expiry), signed `token_amount` in retail-credit USD, `estimated_cost_usd`, `balance_after`, `grant_id` referencing the originating grant transaction, `expires_at`, optional `request_id` FK for a debit. One request may debit multiple lots. |
| `subscriptions` | One monthly subscription; `subscription_id` | `user_id`, `plan`=pro_monthly, `started_at`, optional `cancelled_at`, `amount_usd` (monthly invoice price, not lifetime revenue). |
| `payments` | One successful actual charge; `payment_id` | `user_id`, `subscription_id` FK, `timestamp`, `amount_usd`, `payment_type` (initial/renewal). Source of revenue. |
| `ai_requests` | One attempted request; `request_id` | `user_id`, `timestamp`, `model_type` (standard/premium), physical `input_tokens`/`output_tokens`, `estimated_inference_cost` in USD, `success` 0/1, `session_id`, `credit_spent` in retail-credit USD. Paid requests spend zero free credit; service failures can still incur inference costs. |
| `user_days` | Every observed user × age day; (`user_id`,`age_day`) | `date`, `age_day` (signup=0), `is_active` (session), `is_meaningful` (≥2 successful requests), `requests` (successful count), `inference_cost`, `revenue` (actual charges), `credit_spent`, `bonus_only` (active with zero successful requests). Includes inactive days with zeros. |

Event types: `signup`, `session_start`, `token_grant`, `ai_request` (successful), `ai_request_failed`, `activation` (first meaningful day), `meaningful_usage` (later meaningful day), `subscription_started`, `subscription_renewed`, `subscription_cancelled`. `activation` is a threshold event, not the user's first request. Purchase occurs before the request that triggered funding friction. An automated token grant is not activity and does not qualify for retention.

The schema keeps credit liabilities, actual payment revenue and inference expenses separate. Never sum `subscriptions.amount_usd` to estimate revenue, and never value a grant's retail dollars as inference expense. Retention eligibility uses `observed_days > age_day`; 30-day cumulative conversion uses ages 0–29 and `observed_days >= 30`. D30 retention specifically requires 31 observed days.

Generated relations are checked by `src.validation.assert_valid`: identifiers, foreign keys, assignment consistency, timestamp windows, observed day completeness, signed and cumulative balances, per-request credit debits, and per-day revenue/cost/usage reconciliation. A validation failure is a pipeline error, not a warning to ignore.
