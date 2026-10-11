# Setup and reproduction

Python 3.11–3.13; Python 3.12 is the verified local runtime. No paid services or API keys are needed.

From the repository root:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell instead
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m scripts.pipeline --users 10000 --seed 42 --scenarios
python -m scripts.external
python -m scripts.sensitivity --users 1000 --seeds 42 43 44
python -m pytest -q
python -m ruff check .
python -m streamlit run dashboard/app.py
```

Open http://localhost:8501. First generation can take several seconds. The simulator has no network dependencies. The real dataset is bundled; downloading is necessary only if you remove it. All SQL is executed by the pipeline; outputs are in `data/synthetic/sql-results/` and the database is `data/synthetic/growth_lab.sqlite`. Open that database with any SQLite client to inspect underlying records and run queries.

For the static case study:

```bash
python -m http.server 8000
```

Open http://localhost:8000/case-study/. Use an HTTP server so local JSON downloads work. The case-study source includes the verified release results generated in this package; it does not claim a live experiment.

The baseline configuration and table hashes are recorded in `data/synthetic/manifest.json`. Re-run the same seed, configuration, dependency versions and pipeline to reproduce data. JSON outputs replace NaN with null; a missing denominator stays undefined instead of becoming zero. Gzip uses a fixed timestamp for deterministic artifact hashes. Wall-clock timing is not part of the manifest.

Only top-level dependencies are pinned; `requirements-lock.txt` records the full locally verified resolution. To replicate that exact environment on another Python 3.12 platform, install the lock file; platform-specific wheels still vary. CI verifies from declared development dependencies in an isolated GitHub runner.
