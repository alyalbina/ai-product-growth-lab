# Publication guide and status

Intended GitHub owner: **alyalbina**. Intended repository: **ai-product-growth-lab**. Never change the existing hotel repository.

The authenticated account during preparation was AlbinaResearcher and did not have write permission to alyalbina. Unless `docs/validation.md` records a subsequently verified deployment, this archive is a publication-ready delivery, not an already published repository or public Python demo. Planned URLs must not appear in a CV as live links.

An additional Sites publication attempt stopped at an automatic permission rejection before the source push; no public Site is claimed. The local static case and both interactive reports are complete and included in the ZIP.

## GitHub via command line

Authenticate as alyalbina (or an account explicitly granted creation rights). Do not paste access tokens into files or chat. Create a new empty public repository with the exact name, then from the unpacked project:

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

In repository Settings → Pages, select **GitHub Actions** as the source. The included Pages workflow deploys `case-study/` on main. Confirm its action succeeds, then visit the actual Pages URL and test navigation, downloads and the dashboard link. Pages does not execute Python. The expected URL after deployment is `https://alyalbina.github.io/ai-product-growth-lab/`; this is a proposed address until checked.

## Python dashboard: Streamlit Community Cloud

Create/sign in to an account at https://share.streamlit.io and connect the GitHub account containing this new repository. Deploy the main branch entrypoint `dashboard/app.py`, select Python 3.12 and a custom available subdomain. Community Cloud is free for this public educational portfolio use. Verify the actual deployed URL, not a guessed subdomain, and configure `DASHBOARD_URL` when rebuilding the static case page links.

Checked official documentation on 9 October 2026: [deploying an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), [resource limits and hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app), [status and limitations](https://docs.streamlit.io/deploy/streamlit-community-cloud/status). Published limits can change; current documentation describes shared CPU/memory constraints and hibernation after 12 hours without traffic. This is not an uptime SLA. Keep cached simulations bounded and avoid committing the SQLite database. Recheck current terms before hosting.

After deployment: load each view; filter by a single channel and an empty selection; run a 1,000-user negative scenario; save and compare it; download a CSV; visit the independent public-data view. Check logs and startup memory. Record the working URLs in README, case-study and portfolio materials only after availability is verified.
