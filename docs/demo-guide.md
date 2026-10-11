# Five-minute portfolio walkthrough

1. **Context / 30 seconds.** Open the case study. Say: “A real product question inspired this independent model. These are synthetic users; I do not have a real Monolit experiment result.” Explain equal baseline $5 entitlement and finite five-day distribution.
2. **Overview / 45 seconds.** Compare ordinary D7 with meaningful D7. Read mature denominators. Explain why retention can rise while contribution deteriorates. Explain cash receipts versus promotional credit versus provider cost.
3. **Cohorts / 45 seconds.** Select a late signup week. Show blank D30 cells and the eligibility table. Explain exact-day versus rolling retention, and why a registration cohort is a valid denominator even if some users never return.
4. **Experiment / 60 seconds.** Read the primary risk difference and interval. Check SRM, practical threshold, paid-conversion and contribution guardrails. Point out that the synthetic 10,000-user example is below the assumed 2pp power-plan target and calendar censoring reduces effective sample further. Secondary endpoints use Holm-adjusted p-values; segments are exploratory.
5. **Simulation Lab / 60 seconds.** Run negative with 1,000 users, save the run, then run positive with identical user count. Increase inference-cost multiplier and rerun. Inspect current vs saved scenario data and download outputs. These results are responses of the model to assumptions, not empirical treatment evidence. Changing daily credit amount changes entitlement; it is an economic sensitivity, not the equal-budget primary experiment. Explain the seven-day expiry confound before interpreting D7.
6. **Real evidence / 30 seconds.** Open External real data. Explain what 12,330 real e-commerce sessions can show: purchase conversion and descriptive associations. Explain why they cannot provide user retention or validate AI reward effects.
7. **Technical discussion.** Open the SQL retention query, corresponding Python metric and its edge-case tests. Show the explicit credit ledger and validation, then the offline research report. Read `docs/portfolio.md` for role-specific interview narratives.

Additional reproducible demonstrations:

```bash
# Defaults: mature and censored cohorts
python -m scripts.pipeline --users 10000 --scenarios
# Same treatment/control mechanism: behavioral A/A
python -m scripts.pipeline --users 2000 --scenario aa --output work/aa-release
# Three-seed parameter sensitivity + inference calibration
python -m scripts.sensitivity --users 1000 --seeds 42 43 44
python -m scripts.calibrate
python -m scripts.research
```
