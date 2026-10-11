# Executed verification

This records work actually executed, not a promise that hosted CI passed. Local checks used Python 3.12 on Windows with a fresh virtual environment, pinned packages and `pip check` without dependency conflicts.

| Check | Observed result |
| --- | --- |
| Full pytest suite | 33 passed, 11.54 seconds |
| Final Streamlit AppTest rerun | 3 passed, 14.92 seconds on 11 October 2026 |
| Ruff | All checks passed |
| Baseline pipeline | 10,000 users, seed 42, 90 calendar days; linked tables and financial reconciliation passed |
| Scenario comparison | Full-size positive, neutral and negative runs; negative retention gain blocked by economic guardrails |
| SQL execution | All nine SQL files executed; results included in `data/synthetic/sql-results/` |
| Parameter sensitivity | Seven parameters × three values × three seeds = 63 runs of 1,000 users |
| A/A inference calibration | 1,000 null replications; false-positive rate 5.0%, Wilson interval 3.81%–6.53%; separate behavioral A/A run |
| Real source analysis | 12,330 original UCI sessions; 1,908 purchase sessions; zero missing cells; 125 identical feature rows retained |
| Research artifacts | Nine offline interactive synthetic charts and three separate real-data charts generated from Python outputs |

Tests cover reproducibility, primary/foreign keys, expiry, credit/payment reconciliation, mature and incomplete cohorts, no-event users, empty selections and zero denominators. SQL/Python parity and an ordered-funnel regression verify actual event ordering even within the same day. Statistics are checked against explicit reference calculations; confidence intervals and Holm correction are tested. AppTest renders every dashboard tab and exercises empty filters and scenario recalculation/saving using a bounded real simulation fixture.

On 11 October 2026, the full 1,000-user negative scenario was executed through the actual local browser interface, and saving it displayed the saved/current comparison. The executive CSV was downloaded through the UI and its two rows matched the release summary. The case study was checked at a 410 × 900 viewport: document width 395px, scroll width 395px, no horizontal overflow. Its real-data link opened the separate report with correct provenance and purchase-rate figures. Desktop, mobile and dashboard screenshots are in `docs/screenshots/`. The saved default dataset is included as compressed CSVs in the handoff ZIP; SQLite can be regenerated and is excluded from the ZIP to reduce size.

## Interpretation and verification boundaries

**Synthetic Data — Analytical Simulation, Not Real Company Results.** The default D7 metric coincides with control credit expiry, while later treatment grants can remain until the start of D11. This policy difference is disclosed prominently. Neither statistical significance nor A/A calibration validates a real Monolit effect.

Only Python 3.12 was executed locally. CI definitions cover Python 3.11–3.13, but remote GitHub Actions have not been run. Dependency inputs are pinned; package patch updates and security maintenance remain ordinary future maintenance.

The Python dashboard has been tested locally; a public Streamlit deployment is not verified. GitHub authentication during this task belonged to AlbinaResearcher, with no write permission to the requested alyalbina owner. No repository was created under a substitute owner. The ZIP and `docs/publishing.md` provide the authorized fallback. Public static case publication is recorded below only after successful deployment.

## Static publication attempt

A private, unpublished Sites project was registered. The prepared static source includes the case study and both offline reports. On 11 October 2026, automatic permission review rejected passing the temporary source credential to the official publishing helper through hidden stdin, with `approval required by policy, but AskForApproval::Granular.sandbox_approval is false`. A narrowly scoped permission for the new checkout's Git directory did not resolve that rejection. No source push, saved version or public deployment completed. The registered expected URL is therefore deliberately not presented as a live demo. No token was written into deliverable files. Static files can be opened offline or published with the supplied GitHub Pages workflow after account access is available.
