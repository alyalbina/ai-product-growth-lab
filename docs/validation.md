# Executed verification

This records work actually executed, not a promise that hosted CI passed. Local checks used Python 3.12 on Windows with a fresh virtual environment, pinned packages and `pip check` without dependency conflicts.

| Check | Observed result |
| --- | --- |
| Full pytest suite | 33 passed, 11.54 seconds |
| Final Streamlit AppTest rerun | 3 passed, 20.78 seconds on 11 October 2026 after adding the live GitHub source link |
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

Python 3.12 was executed locally. Remote GitHub Actions also passed on Python 3.11, 3.12 and 3.13 in clean Ubuntu runners: pinned dependency installation, Ruff, all 33 tests, a 250-user three-scenario SQL/pipeline smoke run, and the independent real-data analysis. See [PR checks](https://github.com/alyalbina/ai-product-growth-lab/actions/runs/38150789073) and [main checks](https://github.com/alyalbina/ai-product-growth-lab/actions/runs/38150923989). Dependency inputs are pinned; package patch updates and security maintenance remain ordinary future maintenance.

The public [Streamlit dashboard](https://alyalbina-ai-growth-lab.streamlit.app/) was deployed and verified on 11 October 2026. On 11 October 2026, the owner completed GitHub CLI authentication as alyalbina. The new public repository is [alyalbina/ai-product-growth-lab](https://github.com/alyalbina/ai-product-growth-lab). [PR #1](https://github.com/alyalbina/ai-product-growth-lab/pull/1) was merged after passing CI. The existing Hotel Guest Experience Platform repository was not changed.

## Verified GitHub Pages publication

[The Pages deployment](https://github.com/alyalbina/ai-product-growth-lab/actions/runs/38150924002) succeeded for merge commit `1fe1ac33bb386c7b14122aba2ca4797301e3fe64`. The actual [public case](https://alyalbina.github.io/ai-product-growth-lab/) was then checked in the browser: model results rendered, source link resolved to the correct repository, and the localhost-only dashboard link was hidden. The [synthetic report](https://alyalbina.github.io/ai-product-growth-lab/research.html) rendered nine Plotly charts; the [separate UCI report](https://alyalbina.github.io/ai-product-growth-lab/external.html) rendered three charts with the correct purchase rate and provenance. A screenshot of the published case is included separately in the output folder.

GitHub Pages serves static HTML/JS research outputs. It is not the Python runtime, and its publication does not verify a live scenario simulator. The separate [Streamlit runtime](https://alyalbina-ai-growth-lab.streamlit.app/) now executes the Python dashboard and scenario model.

## Verified Streamlit publication

Deployed from `alyalbina/ai-product-growth-lab`, branch `main`, entrypoint `dashboard/app.py`. Cloud logs confirmed Python 3.12.15 and Streamlit 1.45.1. The sharing dialog showed “Make this app public” checked. The verified address is https://alyalbina-ai-growth-lab.streamlit.app/.

All six tabs rendered. The default model loaded 10,000 users and reproduced the release economics and experiment figures. Channel filtering selected 3,513 organic users; clearing all channels displayed the intended empty-selection message. A real 1,000-user negative model run completed in the hosted UI, compared with a neutral baseline, and saved the current run for comparison. The executive CSV download matched both release rows and all 17 columns within numerical precision (rtol/atol 1e-10). The independent UCI view showed 12,330 sessions and 1,908 purchases. At desktop width 1,440px the document scroll width equaled its viewport width; the narrow interface was also used for the filter checks. The public deployment screenshot is `docs/screenshots/dashboard-cloud.jpg`.

No application traceback was present in the inspected cloud logs during these checks. Peak memory was not measured; this verifies observed startup and a bounded scenario run, not an uptime or load guarantee. The host can hibernate; its Python dependency resolver is distinct from the local lockfile.

## Static publication attempt

A private, unpublished Sites project was registered. The prepared static source includes the case study and both offline reports. On 11 October 2026, automatic permission review rejected passing the temporary source credential to the official publishing helper through hidden stdin, with `approval required by policy, but AskForApproval::Granular.sandbox_approval is false`. A narrowly scoped permission for the new checkout's Git directory did not resolve that rejection. No source push, saved version or public deployment completed. The registered expected URL is therefore deliberately not presented as a live demo. No token was written into deliverable files. Static files can be opened offline or published with the supplied GitHub Pages workflow after account access is available.
