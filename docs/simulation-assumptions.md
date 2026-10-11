# Simulation assumptions

**Synthetic Data — Analytical Simulation, Not Real Company Results.** This independent model uses a product question inspired by the user's account of Monolit. It does not establish that the proposed daily mechanism was deployed, and none of its rows or estimates are Monolit observations.

## Observation and assignment

`Config` is a frozen dataclass; every run records it in each returned DataFrame's `attrs`. The default is 10,000 users, seed 42, and 90 calendar days starting 1 January 2025. Signup is uniform over the entire calendar observation horizon, representing ongoing acquisition. Observation ends at a shared administrative cutoff. `observed_days` counts age days 0 through N−1, so a Dk outcome is eligible only when `observed_days > k`. The youngest cohorts can have only one observed day; D1, D7 and D30 therefore use different eligible denominators even in the baseline. Missing future outcomes must not be treated as churn.

Independent Bernoulli assignment has probability 0.5, rather than an artificially forced exact split. Sample-ratio testing is therefore meaningful. Channels and countries are drawn before behavioral outcomes. Channel influences the segment distribution; segment influences latent product value, request intensity and price sensitivity. These are model assumptions, not estimated market facts. Countries provide descriptive filters and do not encode discriminatory causal rules.

## Credit policy and ledger

Control receives $5 in retail credit at signup. Default treatment automatically receives $1 on age days 0, 1, 2, 3 and 4. Eligibility does not require a visit, return or request. Each grant expires at the beginning of the age day `expiry_days` later (default seven days). Before expiry it can be spent FIFO. This makes the comparable nominal entitlement $5 in both arms without conditioning treatment eligibility on retention.

Grants stop while a paid subscription is active. As a consequence, delivered entitlement can be below $5 for early purchasers; report delivered and spent amounts separately. Paid subscribers receive access to requests rather than new free retail-credit grants. Old free credit may expire while subscribed. Grant timing, expiry and depletion remain different between arms even when total nominal entitlement is equal.

Sensitivity changes intentionally alter the policy: `grant_days` counts grant opportunities, spaced `grant_frequency` age days apart. Thus five opportunities with frequency two occur on age days 0, 2, 4, 6 and 8. `daily_credit * grant_days` is treatment's nominal entitlement. Nondefault unequal entitlements should be interpreted as a different budget hypothesis, never as an equal-budget causal comparison.

`token_amount` is signed **retail-credit dollars**, not physical model tokens and not inference cost. Grants are positive; debits and expiry are negative. The separate `input_tokens` and `output_tokens` are physical AI token counts. Retail request prices are $0.12 standard / $0.32 premium; they represent an illustrative credit schedule, not vendor pricing. Grant and expiry inference cost is zero. Debit `estimated_cost_usd` allocates the funded free request's inference cost across its credit lots. Use `ai_requests.estimated_inference_cost` for total inference cost, including paid and attempted service failures; adding ledger cost would double count.

## Forward-only behavior

Each user is simulated chronologically. At the beginning of a day, the model expires old credit, evaluates a due monthly renewal, and posts eligible grants. Return probability depends on latent value, past meaningful-use days, age decay, recent inactivity, current credit availability, paid status and a small weekly seasonality term. A daily reward adds a decaying novelty component. Signup day has a session; a grant on a subsequent day never guarantees a session. Probabilities are clipped to [0, 0.95]. The `return_multiplier` changes return propensity rather than fabricating activity outcomes.

Active users draw a request count from their segment intensity. A small model-dependent share of treatment sessions have no attempted request: observable low-value reward visits. Request funding is checked before execution. Insufficient funding creates one failed request with zero tokens and zero inference cost; a funded service failure can incur inference cost but spends no credit. Successful free requests debit retail credit; paid requests have no retail-credit debit. Failed requests never count toward activation or retention. Meaningful use is at least two successful requests on a day; `bonus_only` means an active day with zero successful requests (a descriptive proxy, not known user intent).

Purchase attempts arise when a request encounters insufficient credit. Purchase probability depends on latent value, past use, a user budget draw, subscription price and `purchase_multiplier`. Paid users can cancel at a monthly renewal decision. Retained subscriptions produce a new actual charge every 30 days. After cancelling, a user does not resubscribe within this simplified horizon. No future behavior or end-of-horizon outcome enters any transition.

## Cost and revenue

Illustrative inference cost is `(input_tokens * 0.000003 + output_tokens * 0.000012)`, multiplied by 2.4 for premium and by `cost_multiplier`. This is a synthetic marginal-cost schedule. Actual charges live in `payments`; `subscriptions.amount_usd` is an invoice price, never cumulative revenue. Every `user_days` row reconciles successful request count, inference cost, spent free credit and actual payment revenue to source rows. There are no refunds, failed payments, taxes, support or fixed costs. Consequently the dashboard's contribution is **revenue minus inference**, not net profit or full gross margin.

## Scenario assumptions

| Scenario | Reward novelty increment | Learning increment per meaningful day, decayed by age | Treatment purchase propensity multiplier | Reward-visit probability, decayed by age |
|---|---:|---:|---:|---:|
| Positive | 0.16 | 0.055 | 1.20 | 0.07 |
| Neutral | 0.12 | 0.012 | 0.95 | 0.16 |
| Negative | 0.24 | −0.012 | 0.65 | 0.39 |
| A/A | 0 | 0 | 1.00 | 0 |

These are hypothesized response patterns, not fitted treatment effects. Even the positive case can lose because daily grants, expiry, purchase timing, funding friction, inference costs and random sampling jointly determine the result. Scenario names describe assumptions; never promise an economic winner. A/A gives both labels control's grant and behavioral rules. It is an infrastructure sanity check, not evidence of real-world validity. Compare multiple seeds for robustness; do not select a seed after seeing results.

## Reproducibility and limits

NumPy's seeded generator drives every draw; the same code, config and supported dependency versions reproduce tables. Changing policy can change the order of random draws, so two scenario runs with one seed are not a perfectly paired counterfactual comparison. The cost multiplier alone changes cost without changing behavior, which is tested. Country effects, user networks, pricing experimentation, billing failures, advertising spend, dynamic model routing and product quality changes are omitted. The model can test analytic correctness and illuminate trade-offs; it cannot estimate the causal effect at Monolit or forecast a real business without calibration and a prospective randomized experiment.
