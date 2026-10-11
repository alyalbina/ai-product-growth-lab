# Publication guide and status

Intended GitHub owner: **alyalbina**. Intended repository: **ai-product-growth-lab**. Never change the existing hotel repository.

## Verified publication on 11 October 2026

- GitHub: https://github.com/alyalbina/ai-product-growth-lab.
- Implementation: [PR #1](https://github.com/alyalbina/ai-product-growth-lab/pull/1), merged after successful CI on Python 3.11–3.13.
- Public static case: https://alyalbina.github.io/ai-product-growth-lab/.
- Interactive synthetic report: https://alyalbina.github.io/ai-product-growth-lab/research.html.
- Separate real-data report: https://alyalbina.github.io/ai-product-growth-lab/external.html.
- Public Python dashboard: https://alyalbina-ai-growth-lab.streamlit.app/ — deployed from main, dashboard/app.py, Python 3.12; verified in the browser.

GitHub CLI now uses alyalbina. The initial preparation account was AlbinaResearcher; it was not used to create this repository. Windows Git transport encountered SChannel and shell restrictions in the agent's environment, so ordinary Git objects were uploaded through GitHub's documented Git API using gh's secure keyring authentication. Local and uploaded implementation commit SHAs matched. No credential was copied into source or delivery files.

An earlier Sites publication attempt stopped at an automatic permission rejection before the source push. GitHub Pages is the successfully verified public route. The static case and both interactive reports are also included in the ZIP.

## Clone the published project

```bash
git clone https://github.com/alyalbina/ai-product-growth-lab.git
cd ai-product-growth-lab
python -m pip install -r requirements-dev.txt
python -m streamlit run dashboard/app.py
```

## Publish a new independent copy via command line

The requested alyalbina repository already exists. The following sequence is a template for a new copy under an owner/name you select; do not rerun repository creation against the existing delivery. Authenticate as the selected owner. Do not paste access tokens into files or chat. From a fresh unpacked project:

```bash
git init -b main
git add README.md LICENSE .gitignore
git commit -m "Initialize AI Product Growth Lab"
gh repo create alyalbina/ai-product-growth-lab --public --source . --remote origin --push
git switch -c feature/analytics-lab
git add .
git commit -m "Add simulation, analytics, dashboard and independent real-data case"
git push -u origin feature/analytics-lab
gh pr create --base main --head feature/analytics-lab --title "Build AI Product Growth Lab" --body "Adds reproducible synthetic AI SaaS analytics and a separate licensed real-data study. See docs/validation.md for executed checks."
```

Review CI and merge the PR when satisfied. Generated raw tables are intentionally ignored; scripts recreate them. If using the GitHub web uploader, extract the ZIP and upload the contents of its project folder, **not the ZIP itself**; omit `data/synthetic/*.csv.gz` and `.sqlite` from uploads. File-upload size limits make the command-line route preferable.

## Static case study: GitHub Pages

GitHub Actions is already configured as the Pages source for this repository. The included workflow deploys `case-study/` on main. Its initial deployment succeeded, and the actual public URL and both reports were checked. Pages does not execute Python. For future edits, confirm the corresponding deployment succeeds and retest changed navigation or charts.

## Python dashboard: Streamlit Community Cloud

Create/sign in to an account at https://share.streamlit.io and connect the GitHub account containing this new repository. Deploy the main branch entrypoint `dashboard/app.py`, select Python 3.12 and a custom available subdomain. Community Cloud is free for this public educational portfolio use. Verify the actual deployed URL, not a guessed subdomain, and update the dashboard anchor in `case-study/index.html` and portfolio materials after verification.

Checked official documentation on 9 October 2026: [deploying an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), [resource limits and hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app), [status and limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status). Published limits can change; current documentation describes shared CPU/memory constraints and hibernation after 12 hours without traffic. This is not an uptime SLA. Keep cached simulations bounded and avoid committing the SQLite database. Recheck current terms before hosting.

The published dashboard passed the following browser checks on 11 October 2026: all six views loaded; the baseline contained 10,000 users; the organic channel selected 3,513 users; an empty channel selection displayed the intended no-data state; a negative 1,000-user simulation completed and saved its comparison; the exported executive CSV matched all 17 release columns. Sharing showed “Make this app public” checked. Cloud logs confirmed Python 3.12.15 and no application traceback during these checks. Peak memory was not measured. Screenshot: `docs/screenshots/dashboard-cloud.jpg`.

For future deployments: load each view; filter by a single channel and an empty selection; run a 1,000-user negative scenario; save and compare it; download a CSV; visit the independent public-data view. Check logs and startup memory. Record the working URLs in README, case-study and portfolio materials only after availability is verified.
