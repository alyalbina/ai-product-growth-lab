# Experiment design: timing of a fixed $5 credit entitlement

This is a prospective design plus a synthetic worked analysis. No real Monolit experiment or measured business result is asserted. The historical product problem motivates an independent portfolio laboratory; actual implementation of the alternative remains unverified.

## Question and intervention

Can daily token rewards improve meaningful retention and paid conversion without undermining AI product unit economics?

Control receives $5 upfront. Treatment receives $1 on each of five scheduled eligible days; the default grant ages are 0, 1, 2, 3 and 4. Grants are automatic and do not require a return visit; user return is separately simulated. Eligibility is a signup-age schedule, not five self-selected active days. Each grant follows the configured expiry rule. Both policies therefore authorize the same $5 nominal total; timing and unused-credit expiry may still change realized consumption and provider cost. Scenario controls can change frequency, expiry and entitlement size; any unequal-budget configuration is a separate policy question and is labeled as such in analysis.

## Assignment, estimand and eligibility

- Unit: newly registered user; persistent 1:1 Bernoulli assignment at signup.
- Eligible population: all new synthetic users, independent of activity, payment or balance. In a real study, exclude internal and fraud accounts using rules fixed before assignment.
- Primary estimand: treatment minus control probability of meaningful activity on age 7 in the eligible assigned population (ITT).
- Analysis eligibility: complete checkpoint observation; N>7 for the primary. Both cohorts use the same administrative cutoff. No active-user filtering or conditioning on post-treatment balances.
- Calendar: the portfolio simulation enrolls throughout a 90-day observation horizon, so late signups are right-censored. A prospective real study could enroll over 60 days and retain at least 31 days after the final included signup for D30. Novelty should be evaluated after the final grant and with later checkpoints.

The synthetic random generator creates assignment independently of signup, acquisition and latent preference. There is no rerandomization until a desirable result emerges. Real rollout requires stable assignment, cross-device identity and separation of experiment variants from billing side effects.

## Metrics and pre-specified decision rules

Primary: meaningful D7, defined as at least two funded successful requests on age 7. Secondary family: D1, D7, D30 and first-30-day paid conversion. Guardrails: first-30-day contribution per assigned user, paid conversion and bonus-only active-day share. The meaningful proxy is deliberately conservative and needs validation against real completed jobs.

For this worked design, advance to a **real controlled pilot** only if all conditions hold:

1. No sample ratio mismatch at α=0.001, using all assigned users.
2. Primary two-sided p<0.05 and the 95% risk-difference CI lies above zero.
3. Primary estimated absolute uplift is at least 2 percentage points.
4. The 95% lower bound for contribution difference is no worse than −$0.25 per assigned user over 30 days.
5. The 95% lower bound for paid-conversion difference is no worse than −1 percentage point.
6. Bonus-only share increases by at most 10 percentage points (a descriptive guardrail; a production protocol should add user-clustered uncertainty).

These tolerances are explicit portfolio assumptions, not approved company economics. They should be revised before real enrollment using inference budgets and customer value. A passing simulation can motivate a real test, never prove the intervention works. The protocol can return inconclusive even with significant retention; it does not guarantee a winning policy.

## Inference and planning

Binary outcomes use a two-sided pooled two-proportion score test and the Newcombe hybrid-score difference interval constructed from Wilson score intervals. This handles 0% and 100% rates more reliably than an unbounded Wald interval; the choice follows [Newcombe's comparison of independent-proportion intervals](https://pubmed.ncbi.nlm.nih.gov/9595617/). CI and test may differ slightly near decision boundaries; the decision requires both. Undefined denominators remain undefined.

The four secondary p-values receive Holm step-down family-wise adjustment at α=0.05. An unobservable checkpoint retains its slot in the pre-specified four-test family, while its p-value remains undefined; administrative censoring must not silently shrink the correction. The primary hypothesis is separate and fixed in advance. Guardrail intervals are individual 95% intervals used conservatively together; exploratory segment cuts carry no confirmatory significance claim and require a preregistered interaction test or a follow-up experiment.

Contribution inference uses **one outcome per assigned mature user**, including zeros for inactive users. A Welch t interval estimates the mean difference; a seeded user-level percentile bootstrap provides a skew sensitivity check. Bootstrap runs are bounded to 100–1,000 iterations to keep the dashboard responsive. The point estimate uses the full population; there is no winsorization or positive-revenue-only conditioning. Extreme skew in real billing can require more resampling and robust modeling.

Planning assumes control meaningful D7=20%, target treatment=22%, two-sided α=0.05 and power=80%. The normal two-proportion planning approximation yields about **6,510 eligible users per arm**, roughly 13,020 total. Execute `power_plan()` for the exact rounded calculation. The default 10,000-user simulation is therefore **below this target** and should not be described as an adequately powered real experiment. Additional immature signups, exclusion rates or fraud require enrollment inflation. The 20% baseline is a planning assumption; changing the synthetic scenario can yield a different baseline and achieved power.

## A/A and sensitivity

`aa_calibration()` runs seeded independent Bernoulli null experiments and reports the empirical false-positive rate, its Wilson interval and the p-value distribution. It tests calibration of the score procedure at the specified sample size, not realism of the behavioral model. The generator's `aa` scenario applies the control policy to both labels for a separate end-to-end check; one run can still show random differences.

Compare positive, neutral and negative economic scenarios under the same seed. Change entitlement amount, schedule, expiry, cost multiplier, price, return and purchase parameters one at a time or as explicit policy packages. Results are conditional on those assumptions, not causal discoveries about real users. Real pilot analysis should monitor assignment integrity, payment logging and outages; avoid repeated significance peeking, fix the horizon or adopt a properly designed sequential procedure.

## What could invalidate a real readout?

Nonrandom missing logs, interference through shared accounts, treatment-specific assignment bugs, unavailable models, unequal marketing, early stopping and payment refunds can bias results. A real study needs data contracts, preregistered exclusions, reconciliation to payment processors, an event-loss audit and long-term follow-up. A 30-day contribution result omits longer subscription survival and acquisition economics. Reward-driven activity after day 4 could persist, decay or crowd out payment; synthetic behavior cannot decide which occurs in production.
