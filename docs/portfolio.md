# CV, LinkedIn and interview preparation

This is independent portfolio work, built with AI engineering assistance. Monolit experience motivated the question; no preserved Monolit logs, experimental results or verified rollout are represented. Review the implementation and reproduce it before presenting technical ownership in an interview. Link slots below remain unpublished until verified.

## English CV

- Built a reproducible product analytics lab modeling 10,000 synthetic AI SaaS users over 90 calendar days; designed linked behavioral, credit, subscription and inference-cost data with automated reconciliation.
- Implemented censoring-aware SQL and Python analyses of activation, retention, paid conversion and contribution; evaluated randomized synthetic experiments with confidence intervals, sample-ratio checks and multiple-comparison correction.
- Developed an interactive scenario dashboard and a separate analysis of 12,330 licensed UCI e-commerce sessions, explicitly distinguishing simulation outputs from observed real-world evidence.

**Technical skills:** Python, SQL (SQLite), pandas, NumPy, SciPy, Plotly, Streamlit, cohort analysis, metric design, experiment design, power analysis, confidence intervals, unit economics, data validation, pytest, Ruff, GitHub Actions.

**GitHub:** https://github.com/alyalbina/ai-product-growth-lab. **Demo:** add the verified Streamlit URL. **Case study:** add the verified Pages URL. Do not present these outputs as Monolit business impact.

## LinkedIn

**Project description:** AI Product Growth Lab explores whether distributing free AI credits over several days could improve meaningful retention without damaging product economics. I structured an independent synthetic-data study, designed an auditable credit and cost model, and implemented SQL/Python analytics, statistical checks and an interactive dashboard. A separate UCI session study demonstrates work with real public data. The model is a research and decision-design exercise, not evidence of a deployed Monolit experiment.

**Skills:** Product Analytics · Growth Strategy · SQL · Python · Experiment Design · Cohort Analysis · Monetization · Unit Economics · Data Quality · Streamlit.

**Featured description:** Explore a transparent AI SaaS analytics portfolio: inspect cohorts, challenge assumptions, compare retention with contribution, and review the proposed real-world experiment. Synthetic results are clearly labeled; real-data analysis is separate.

## Product Analyst interview story

“In my product context at Monolit, I encountered a concern about users consuming an upfront free balance and then not returning. I did not retain the company's event data and cannot claim a measured effect or confirmed rollout. For this independent project I translated the question into a testable design: equal baseline credit entitlement, user-level randomization, meaningful D7 retention and economic guardrails. I built a reproducible model and checked SQL against Python. The key analytical distinction is returning to use the product versus returning without successful AI use. I would treat simulated results as a way to challenge measurement and assumptions before collecting real data.”

## Growth PM interview story

“A reward can create a habit, but it can also attract subsidized low-value usage or replace paid demand. I compared distributions of the same promotional entitlement rather than an unlimited subsidy. I would launch only after verifying instrumentation, identity and balance accounting, and only if a practically useful retention gain survives contribution and paid-conversion guardrails. The project demonstrates how I make the decision reviewable; it does not assert achieved commercial growth.”

## SQL and Python explanation

Start with `sql/retention/day_retention.sql`: the eligible cohort includes registered users who have enough observation time, including users without events. Explain why a LEFT JOIN and conditional aggregation avoid excluding churned users. Then compare the SQL result with `src/analytics/metrics.py` and its edge-case tests. Explain the difference between signup-cohort filters and selecting only active users. Show daily calendar windows separately from user-age windows.

Open `src/simulation/engine.py`: user state advances one day at a time. Successful funded requests update experience and future return probability; retail-credit lots expire and are consumed separately from inference cost. Payments occur at purchase/renewal and cancellation ends further subscription service. Point to validation reconciliation rather than reading every line.

## Experimentation deep dive

“The unit is a newly eligible account and the estimand is the intention-to-treat difference in meaningful D7 retention among mature signup cohorts. I use a fixed analysis, a two-sided primary test, risk-difference confidence interval, separate SRM validity check, and adjusted secondary comparisons. User-level contribution uses a common first-30-day window with a bootstrap skew check. Cohort maturity is based on administrative observation time, not on activity. Segment differences are exploratory, not a collection of uncorrected rollout decisions. A/A checks test the inference pipeline under a null simulation.”

**Why this experiment design?** “The mechanism redistributes a promotional budget; it should not silently increase total entitlement. Account randomization keeps assignment stable, ITT preserves users who never redeem credits, and meaningful D7 reduces the temptation to celebrate reward-only visits. A common 30-day economic window avoids comparing longer-observed cohorts with shorter ones. Power and duration are planned before looking at results, and guardrails prevent a retention win from overriding economic harm.”

**What did the model reveal about the design?** “D7 coincides with the control credit expiry while later treatment grants remain available. A large modeled D7 lift therefore cannot isolate habit formation. I would align final expiry cutoffs or explicitly test the bundled policy, and preregister a post-reward D14/D30 endpoint. Expiry sensitivity makes that limitation visible rather than hiding it behind significance.”

**What would you do differently with real data?** “First validate identity, event completeness, model prices and billing refunds. Estimate baseline rates and variance from mature historical cohorts, run an A/A instrumentation check, update power using real acquisition volume, and preregister meaningful-use criteria based on actual customer value. Address multiple accounts, country/time-zone boundaries, interference, attribution and fraud. Track provider failures, user satisfaction and post-reward D30 behavior. Use observed costs and refunds instead of hypothetical prices. Simulated return parameters cannot identify the real treatment effect.”
