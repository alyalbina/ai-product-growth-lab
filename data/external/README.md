# Independent real-data study

**Source:** C. Sakar & Y. Kastro (2018), *Online Shoppers Purchasing Intention Dataset*, UCI Machine Learning Repository. DOI: [10.24432/C5F88Q](https://doi.org/10.24432/C5F88Q).

Dataset page: https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset

**License:** [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The original CSV is included unchanged with attribution. The authors describe 12,330 sessions, each from a different user over a one-year period. Downloaded 9 October 2026. `analysis.json` records its SHA-256 hash, completeness, identical feature rows, numerical extremes and group conversion confidence intervals.

The source contains 17 features and a Boolean purchase label. `Revenue` is **not dollars**. There are no precise timestamps, durable user IDs, ordered event streams or transaction amounts. Consequently we do not compute retention, an ordered funnel, ARPU, or an A/B treatment effect from it. Returning_Visitor is a source-provided category, not an observed repeat visit in this file.

Identical feature vectors are reported and retained: without identifiers they cannot reliably be classified as duplicate records. Conversion comparisons across visitor category, traffic type and month are observational and subject to selection/confounding. Months are categories within an unspecified historical year, not a current market time series. PageValues may encode information related to purchase; it is excluded from any proposed pre-treatment causal adjustment. No machine-learning prediction claim is made.

This dataset never joins the synthetic AI SaaS tables. Findings cannot validate AI-token reward hypotheses.

Reproduce: `python -m scripts.external`. A bundled CSV permits offline reproduction. Delete it only if you intentionally want to download the original again.
