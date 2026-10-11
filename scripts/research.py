"""Generate an offline interactive analytical report from actual simulated tables."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
from plotly.offline import get_plotlyjs

from src.analytics.metrics import activity, cohort_heatmap, filter_tables, retention, user_outcomes

PALETTE = {"control": "#087f82", "treatment": "#be7b24"}


def build():
    folder = Path("data/synthetic")
    names = ["users", "events", "token_transactions", "subscriptions", "ai_requests",
             "experiment_assignments", "payments", "user_days"]
    tables = {name: pd.read_csv(folder / f"{name}.csv.gz") for name in names}
    users = tables["users"]
    out = user_outcomes(tables)
    mature = out[out.observed_days >= 30]
    segments = mature.groupby(["experiment_group", "user_segment"]).agg(
        users=("user_id", "count"), paid=("paid", "sum"),
        revenue=("revenue", "sum"), inference_cost=("inference_cost", "sum"),
        meaningful_d7=("meaningful_d7", "mean"), requests=("requests", "sum")).reset_index()
    segments["contribution_per_user"] = (segments.revenue-segments.inference_cost)/segments.users
    segments["margin"] = (segments.revenue-segments.inference_cost).div(segments.revenue.replace(0, float("nan")))
    segments.to_csv(folder / "segment-profitability.csv", index=False)
    eda = {"rows": {name: len(frame) for name, frame in tables.items()},
           "nulls": {name: frame.isna().sum().to_dict() for name, frame in tables.items()},
           "users_by_channel": users.acquisition_channel.value_counts().to_dict(),
           "users_by_segment": users.user_segment.value_counts().to_dict(),
           "observed_days": users.observed_days.describe().to_dict(),
           "successful_requests_per_user_30d": mature.requests.describe(percentiles=[.5, .9, .99]).to_dict(),
           "cash_revenue_per_user_30d": mature.revenue.describe(percentiles=[.5, .9, .99]).to_dict(),
           "note": "Null session IDs on non-session events and null uncancelled subscription dates are structural, not data loss. Extremes are reported rather than silently trimmed."}
    (folder / "eda.json").write_text(json.dumps(eda, indent=2), encoding="utf-8")
    sections = []

    def add(title, description, fig):
        fig.update_layout(paper_bgcolor="#fbfaf7", plot_bgcolor="#fbfaf7",
                          font={"family": "Arial", "color": "#19383a"}, height=410,
                          margin={"l": 45, "r": 20, "t": 20, "b": 40})
        sections.append(f"<section><h2>{title}</h2><p>{description}</p>"+
                        fig.to_html(full_html=False, include_plotlyjs=False)+"</section>")

    heat = cohort_heatmap(tables).pivot(index="cohort", columns="age_day", values="rate")
    add("01 / Mature cohort retention", "Weekly signup cohorts; blank cells have no eligible users. Partially mature cells include only eligible accounts. Daily active retention, pooled arms.",
        px.imshow(heat, color_continuous_scale="Teal", zmin=0, zmax=1,
                  labels={"x": "User age day", "y": "Signup week", "color": "Retention"}))
    curves = retention(tables, days=list(range(1, 61)), meaningful=True)
    add("02 / Meaningful retention curves", "Two or more successful AI requests on an exact user-age day; denominators shrink with administrative observation time.",
        px.line(curves, x="age_day", y="rate", color="variant", color_discrete_map=PALETTE,
                hover_data=["eligible", "retained"]))
    add("03 / Calendar activity", "DAU reflects cumulative acquisition and modeled weekday variation; it is not an experiment treatment estimate.",
        px.line(activity(tables), x="date", y="dau", color="variant", color_discrete_map=PALETTE))
    add("04 / Return frequency", "All mature registered users, including never-active accounts. First 30 user-age days. Histograms avoid active-user conditioning.",
        px.histogram(mature, x="active_days", color="experiment_group", barmode="overlay", nbins=30,
                     color_discrete_map=PALETTE))
    add("05 / Engagement distribution", "Successful funded requests in the first 30 days; tail values are preserved.",
        px.histogram(mature, x="requests", color="experiment_group", barmode="overlay", nbins=45,
                     color_discrete_map=PALETTE))
    add("06 / Revenue distribution", "Cash receipts, not recognized accounting revenue. Most free accounts generate no receipts; renewals after age29 are excluded.",
        px.histogram(mature, x="revenue", color="experiment_group", barmode="group", nbins=25,
                     color_discrete_map=PALETTE))
    add("07 / Segment profitability", "Exploratory first-30-day contribution per mature account. Small subgroup results are not powered rollout recommendations.",
        px.bar(segments, x="user_segment", y="contribution_per_user", color="experiment_group",
               barmode="group", color_discrete_map=PALETTE, hover_data=["users", "paid", "margin"]))
    rows = []
    for variant in ["control", "treatment"]:
        view = filter_tables(tables, mature.loc[mature.experiment_group == variant, "user_id"])
        d = view["user_days"]
        count = len(view["users"])
        successful = d.loc[d.requests > 0, "user_id"].nunique()
        repeated = int((d[d.requests > 0].groupby("user_id").age_day.nunique() >= 2).sum())
        paid = int(mature.loc[mature.experiment_group == variant, "paid"].sum())
        for step, total in [("Registered", count), ("Successful AI use", successful), ("Use on ≥2 days", repeated), ("Paid", paid)]:
            rows.append({"variant": variant, "step": step, "users": total})
    add("08 / Conversion milestones", "Registered and billing counts use mature ITT accounts. These are marginal milestones; paid is not necessarily a subset of repeat-use accounts. Inspect ordered SQL funnel separately.",
        px.bar(pd.DataFrame(rows), x="step", y="users", color="variant", barmode="group", color_discrete_map=PALETTE))
    sensitivity = folder / "sensitivity.csv"
    if sensitivity.exists():
        frame = pd.read_csv(sensitivity)
        add("09 / Economic sensitivity", "One factor at a time, three seeds per value; plotted mean and range reflect model response, not real causal evidence. Changing daily amount changes treatment entitlement.",
            px.strip(frame, x="value", y="contribution_per_user_effect", color="parameter",
                     facet_col="parameter", facet_col_wrap=3, hover_data=["seed"], stripmode="overlay"))
    target = Path("case-study/research.html")
    html = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Research notebook — AI Product Growth Lab</title><style>body{margin:0;background:#fbfaf7;color:#19383a;font:16px/1.65 Arial}main{max-width:1080px;margin:auto;padding:40px 24px}h1{font-size:44px;line-height:1.1;letter-spacing:-2px}h2{font-size:24px}section{padding:28px 0;border-top:1px solid #d5dfda}.notice{padding:12px;background:#e6eee8;font-weight:600}a{color:#087f82}p{max-width:800px}.plotly-graph-div{width:100%}</style><main><a href="index.html">← Product case study</a><p class="notice">Synthetic Data — Analytical Simulation, Not Real Company Results</p><h1>Inspect the evidence.</h1><p>Executed Python analytical modules · fixed seed 42 · 10,000 modeled accounts · 90 calendar days. Explore chart hover, zoom and exports. All measurements describe the supplied model and its assumptions.</p>"""
    target.write_text(html+"<script>"+get_plotlyjs()+"</script>"+"".join(sections)+"</main></html>", encoding="utf-8")
    print(f"Created {target} with {len(sections)} analytical figures")


if __name__ == "__main__":
    build()
