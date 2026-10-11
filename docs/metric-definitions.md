# Metric definitions

All laboratory measures describe **synthetic analytical simulations**, never company results. Dates are UTC calendar dates. The randomized unit is the user. Always filter all user-linked tables together with `filter_tables`; filtering active users alone changes the estimand.

## Observation and eligibility

`observed_days=N` means user ages 0 through N−1 are observed. D7 therefore requires N>7; D30 requires N>30. Registration occurs at age zero. An eligible user with no events is a non-returner, not a missing record. An empty denominator produces NaN in Python and NULL in SQL; dashboards should display an em dash rather than 0%.

Exact-day retention uses all assigned users whose checkpoint is observed. The default 90-calendar-day simulation spreads signups across the full horizon; late signups produce right-censored cohorts and are excluded only at checkpoints they have not reached. Eligibility depends on signup date and calendar cutoff, never future activity.

## Engagement and retention

| Metric | Numerator | Denominator / window |
|---|---|---|
| D1 / D7 / D30 | Assigned users active on exactly that age | Users with the complete checkpoint observed |
| Meaningful D7 (primary) | Users with at least two successful funded AI requests on age 7 | Users with N>7 |
| Weekly cohort heatmap | Active eligible users at each checkpoint | Eligible users in ISO signup week; Python combines arms, SQL offers monthly arm-level cohorts |
| Rolling retention | At least one active day from checkpoint through age 30 | Same N>30 population at every checkpoint; fixed inclusive horizon |
| DAU | Unique active users on a calendar date | No denominator |
| WAU / MAU | Unique active users in trailing 7 / 30 calendar dates, including current date | Counts users once, not sums of DAU |
| Stickiness | DAU | Trailing MAU; undefined if MAU=0 |
| Sessions per user | Distinct observed session IDs per user | All 30-day mature assigned users; signup events without session IDs do not count |
| Requests per user | Successful funded requests in first 30 days | All 30-day mature assigned users |
| Bonus-only rate | Active user-days with no successful request | All active user-days in first 30 days for mature users |

`bonus_only` is an operational proxy for low-value engagement, not a verified measure of user intent. One successful request can still be useful even though it does not satisfy the conservative two-request meaningful threshold. Product validation should examine completed jobs and qualitative feedback.

Returns after grants are the active share on the **next calendar day**, excluding grants whose next full day is censored. Grants overlap in daily treatment, and propensity to return affects bonus uptake. This association is descriptive; it does not identify the causal effect of a particular grant. SQL flags overlapping grant windows explicitly.

## Conversion and economics

Executive financial measures and free-to-paid conversion use **mature first-30-day ITT outcomes**, ages 0–29, for users with N≥30. This differs deliberately from exact D30 retention, which needs age 30 observed. Comparisons do not reward earlier signup with longer exposure.

| Metric | Definition |
|---|---|
| Paid conversion | Users with a positive payment in [signup, signup+30 days) / all mature assigned users |
| Revenue | Sum of actual synthetic `payments.amount_usd` in that window; cash collections rather than accrual revenue |
| Inference cost | Sum of request-level provider costs, including failed attempts, reconciled to daily costs |
| Contribution | Revenue minus inference cost |
| Contribution margin | Contribution / revenue; undefined with zero revenue |
| ARPU | Revenue / all mature assigned users |
| ARPPU | Revenue / unique paying users |
| Cost per active user | Inference cost / users with any active first-30-day day |
| Revenue-to-cost ratio | Revenue / inference cost; undefined with zero inference cost |

Subscription `amount_usd` is the monthly plan price. It must never be summed as lifetime revenue. Renewable billing is recorded in payments. This contribution excludes acquisition spend, payroll, hosting, payment fees, tax and other overhead, so it is not a complete business profit measure. Future LTV is not estimated by multiplying a short-term rate.

Token grants represent a retail credit entitlement, not an immediate provider cost. Debit transactions track actual credit consumption; expiry tracks unused credit. Provider cost can differ substantially from retail credit spent. Summing grants as an expense would overstate inference cost and double-count later usage.

The conversion SQL keeps all mature registered users and calculates first successful request, first meaningful achievement, later-day meaningful repeat and first positive payment. A meaningful achievement occurs at the exact timestamp of that day's second successful request; a noon payment preceding a 15:00 second success is not a payment after repetition. `repeat_then_paid` compares these exact timestamps; overall paid conversion does not condition on activation. There is no separate trial subscription state in this simulation, so a trial-to-paid claim would be unsupported.

## Filters and interpretation

Signup date, channel, segment, country and variant filters subset the same assigned users across all tables. Calendar activity charts show those cohorts' activity rather than every user who happened to be active on the displayed date. A small filtered subgroup can lack one arm or a mature denominator; inference then remains undefined. Segment comparisons are exploratory and do not inherit confirmatory significance.
