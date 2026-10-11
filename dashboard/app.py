"""Run from repository root: streamlit run dashboard/app.py."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.metrics import activity, cohort_heatmap, retention, summarize  # noqa: E402
from src.simulation.engine import Config, simulate  # noqa: E402

DISCLAIMER = "Synthetic Data — Analytical Simulation, Not Real Company Results"
COLORS = {"control": "#087f82", "treatment": "#be7b24"}
LABELS = {"control": "Control · $5 upfront", "treatment": "Treatment · $1 × 5 days"}
st.set_page_config(page_title="AI Product Growth Lab", page_icon="◉", layout="wide")


@st.cache_data(max_entries=2, show_spinner=False)
def load_baseline() -> dict[str, pd.DataFrame]:
    """Load complete published tables, or regenerate the documented fixed-seed run."""
    source = ROOT / "data" / "synthetic"
    # Request/event fact tables remain downloadable in the release; this view
    # needs daily outcomes plus the original monetary ledgers, not every event.
    names = ["users", "token_transactions", "experiment_assignments", "user_days", "payments"]
    paths = {name: source / f"{name}.csv.gz" if (source / f"{name}.csv.gz").exists()
             else source / f"{name}.csv" for name in names}
    if all(path.exists() for path in paths.values()):
        return {name: pd.read_csv(path) for name, path in paths.items()}
    generated = simulate(Config(n_users=10_000))
    return {name: generated[name] for name in names}


def filter_tables(tables, channels, segments, start, end):
    users = tables["users"]
    dates = pd.to_datetime(users["signup_date"]).dt.date
    selected = users.loc[users["acquisition_channel"].isin(channels)
                         & users["user_segment"].isin(segments)
                         & dates.between(start, end)]
    ids = set(selected["user_id"])
    return {name: frame[frame["user_id"].isin(ids)].copy()
            if "user_id" in frame.columns else frame.copy()
            for name, frame in tables.items()}


def chart(fig, height=340):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"family": "Arial, sans-serif", "size": 12, "color": "#35494a"},
                      margin={"l": 12, "r": 12, "t": 30, "b": 30},
                      legend={"orientation": "h", "y": 1.13, "x": 0},
                      hoverlabel={"bgcolor": "#ffffff"})
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#e2e5df", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)


def download(frame, label, filename, key):
    st.download_button(label, frame.to_csv(index=False).encode("utf-8"), filename,
                       "text/csv", key=key)


def percent(value):
    return "—" if pd.isna(value) else f"{value:.1%}"


def money(value):
    return "—" if pd.isna(value) else f"${value:,.2f}"


def variant_table(frame):
    result = frame.copy()
    if "variant" in result.columns:
        result["variant"] = result["variant"].map(LABELS).fillna(result["variant"])
    return result


def arm_tables(tables, variant):
    ids = set(tables["users"].loc[tables["users"]["experiment_group"] == variant, "user_id"])
    return {name: frame[frame["user_id"].isin(ids)].copy()
            if "user_id" in frame.columns else frame.copy() for name, frame in tables.items()}


def render_external():
    st.subheader("A separate evidence track")
    st.write("Real e-commerce sessions from UCI's Online Shoppers Purchasing Intention dataset. "
             "These records are never joined to the AI simulation. Session associations do not establish causality.")
    location = ROOT / "data" / "external" / "analysis.json"
    st.caption("Source: UCI Machine Learning Repository · Dataset 468 · CC BY 4.0 · 12,330 sessions")
    st.markdown("[Dataset, license and attribution](https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset)")
    if location.exists():
        analysis = json.loads(location.read_text(encoding="utf-8"))
        # Keep the full independently reproducible findings inspectable.
        metrics = st.columns(3)
        metrics[0].metric("Real sessions", f"{analysis.get('sessions', 0):,}")
        metrics[1].metric("Purchase sessions", f"{analysis.get('purchases', 0):,}")
        metrics[2].metric("Session purchase conversion", percent(analysis.get("conversion", float("nan"))))
        groups = analysis.get("groups", {}).get("VisitorType", [])
        if isinstance(groups, list) and groups:
            frame = pd.DataFrame(groups)
            chart(px.bar(frame, x="group", y="conversion", color_discrete_sequence=[COLORS["control"]],
                         hover_data=["sessions", "purchases", "ci_low", "ci_high"],
                         labels={"group": "Recorded visitor type", "conversion": "Session purchase conversion"}))
            st.dataframe(pd.DataFrame(groups), hide_index=True, use_container_width=True)
        st.write("The source has no stable user identifier or session timestamp; person-level retention, "
                 "ordering of repeated visits and experimental lift cannot be estimated.")
        with st.expander("Read the reproducible external analysis", expanded=not bool(groups)):
            st.json(analysis)
        st.download_button("Download external analysis", json.dumps(analysis, indent=2),
                           "external_analysis.json", "application/json")
    else:
        st.info("External analysis has not been generated. Run python -m scripts.external "
                "from the repository root; see the setup guide for the source download.")


def render_lab():
    st.subheader("Change the assumptions. Recalculate the trade-off.")
    st.write("A sensitivity exercise, not an estimate of real product impact. Runs share the same seed, "
             "assignment and channel draws; later user behavior is re-simulated as assumptions change. "
             "This is an unpaired scenario comparison. The default grant budget is $5 per arm.")
    with st.form("simulation_form"):
        a, b, c = st.columns(3)
        scenario = a.selectbox("Behavioral scenario", ["positive", "neutral", "negative"], index=1)
        n_users = b.select_slider("Simulation size", [1000, 2000, 3000, 4000, 5000], value=3000)
        seed = c.number_input("Random seed", 1, 100000, 42)
        a, b, c = st.columns(3)
        daily = a.slider("Credit per grant ($)", 0.25, 2.0, 1.0, 0.25)
        frequency = b.slider("Days between grants", 1, 7, 1)
        expiry = c.slider("Credit expiry (days)", 1, 30, 7)
        a, b, c = st.columns(3)
        cost = a.slider("Inference cost multiplier", 0.5, 3.0, 1.0, 0.1)
        price = b.slider("Monthly subscription ($)", 5, 40, 19)
        returns = c.slider("Return propensity multiplier", 0.5, 1.5, 1.0, 0.05)
        purchases = st.slider("Purchase propensity multiplier", 0.5, 1.5, 1.0, 0.05)
        submitted = st.form_submit_button("Run simulation", type="primary")
    st.caption("Compute cap: 5,000 users × 90 calendar days. Five grants only; the control's $5 upfront "
               "grant stays fixed. Changing credit size changes the total treatment entitlement.")
    if submitted:
        settings = dict(n_users=n_users, horizon_days=90, seed=int(seed), scenario=scenario,
                        daily_credit=daily, grant_days=5, grant_frequency=frequency,
                        expiry_days=expiry, cost_multiplier=cost, subscription_price=price,
                        return_multiplier=returns, purchase_multiplier=purchases)
        config = Config(**settings)
        with st.spinner("Simulating users, credit ledgers and inference costs…"):
            current = simulate(config)
            baseline = simulate(Config(n_users=n_users, horizon_days=90, seed=int(seed), scenario="neutral"))
            st.session_state["lab_run"] = {"summary": summarize(current),
                                           "baseline": summarize(baseline), "config": asdict(config)}
        st.success("Simulation completed. Results below use this form's full population.")
    run = st.session_state.get("lab_run")
    if run:
        st.caption("Global signup filters apply to the analytical tabs; the lab evaluates its own complete run.")
        st.write("**Run configuration**")
        st.json(run["config"], expanded=False)
        current = run["summary"].assign(run="Current")
        baseline = run["baseline"].assign(run="Default neutral baseline")
        comparison = pd.concat([baseline, current], ignore_index=True)
        chart(px.bar(comparison, x="variant", y="contribution", color="run", barmode="group",
                     color_discrete_sequence=["#9aabaa", "#087f82"],
                     labels={"variant": "Randomized arm", "contribution": "Contribution ($)"}))
        st.dataframe(variant_table(comparison), hide_index=True, use_container_width=True)
        download(comparison, "Download scenario comparison", "scenario_comparison.csv", "lab_download")
        if st.button("Save current run for comparison"):
            st.session_state["saved_run"] = {"summary": run["summary"].copy(), "config": run["config"].copy()}
            st.success("Saved in this session. Run another scenario to compare.")
        saved = st.session_state.get("saved_run")
        if saved:
            st.write("**Current vs saved run**")
            st.caption(f"Saved: {saved['config']['scenario']} · seed {saved['config']['seed']} · "
                       f"{saved['config']['n_users']:,} users. Different seeds/populations are descriptive comparisons.")
            st.dataframe(variant_table(pd.concat([saved["summary"].assign(run="Saved"),
                                                 current], ignore_index=True)), hide_index=True, use_container_width=True)
    else:
        st.info("Choose assumptions and run the simulation to produce a real calculation.")


def main():
    st.markdown("""<style>
    .block-container {padding-top:2.3rem; padding-bottom:4rem; max-width:1450px;}
    h1 {font-size:2.65rem!important; letter-spacing:-.055em; line-height:1.05!important;}
    h2,h3 {letter-spacing:-.025em;}
    .eyebrow {font-size:11px; letter-spacing:.17em; text-transform:uppercase; color:#58706f;}
    .disclaimer {padding:11px 14px; border:1px solid #d4dbd1; background:#eff2e9;
                 color:#344b40; font-size:12px; margin:18px 0;}
    .lede {font-size:17px; max-width:740px; line-height:1.55; color:#5b6967;}
    [data-testid="stMetricValue"] {font-size:1.75rem; letter-spacing:-.05em;}
    [data-testid="stMetricLabel"] {font-size:12px; color:#657672;}
    [data-testid="stSidebar"] {border-right:1px solid #dce1d9;}
    .stTabs [data-baseweb="tab-list"] {gap:24px; border-bottom:1px solid #dce1d9;}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Independent product analytics / 2026</div>', unsafe_allow_html=True)
    st.title("AI Product Growth Lab")
    st.markdown('<div class="lede">Retention, monetization & experimentation.<br>Do daily AI credits build '
                'lasting value—or only a reason to claim the next bonus?</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)
    with st.spinner("Loading the reproducible analytical dataset…"):
        tables = load_baseline()
    users = tables["users"]
    dates = pd.to_datetime(users["signup_date"]).dt.date
    with st.sidebar:
        st.markdown("### Observation lens")
        st.caption("Filter signup cohorts. All eligible follow-up days remain available.")
        channels = st.multiselect("Acquisition channel", sorted(users["acquisition_channel"].unique()),
                                  default=sorted(users["acquisition_channel"].unique()))
        segments = st.multiselect("User segment", sorted(users["user_segment"].unique()),
                                  default=sorted(users["user_segment"].unique()))
        window = st.date_input("Signup dates", value=(dates.min(), dates.max()),
                               min_value=dates.min(), max_value=dates.max())
        st.divider()
        st.caption("Control · 5 USD upfront\n\nTreatment · 1 USD daily for five eligible days")
        st.caption("Randomization unit: user. Incomplete retention windows are excluded from their day-specific denominators.")
        st.link_button("View source on GitHub", "https://github.com/alyalbina/ai-product-growth-lab")
    start, end = (window[0], window[-1]) if isinstance(window, (list, tuple)) and window else (dates.min(), dates.max())
    filtered = filter_tables(tables, channels, segments, start, end)
    st.caption(f"{len(filtered['users']):,} / {len(users):,} users selected · "
               f"Signup cohorts {start:%d %b %Y}–{end:%d %b %Y} · seed-based model")
    overview, cohorts, experiment, monetization, lab, external = st.tabs(
        ["Overview", "Cohorts", "Experiment", "Monetization", "Simulation lab", "External real data"])
    if filtered["users"].empty:
        for tab in [overview, cohorts, experiment, monetization]:
            with tab:
                st.info("No users match this selection. Expand the channel, segment or signup date filters.")
        with lab:
            render_lab()
        with external:
            render_external()
        return
    summary = summarize(filtered)
    retained = retention(filtered, days=[1, 7, 30])
    meaningful = retention(filtered, days=[1, 7, 30], meaningful=True)
    with overview:
        st.subheader("A return is useful only when it creates value.")
        st.info("Interpret D7 carefully: with a seven-day grant TTL, the control grant expires at the start "
                "of D7 while treatment grants can remain available until the start of D11. The contrast includes "
                "credit availability and does not isolate habit formation. Inspect post-reward D14/D30; "
                "a real pilot should align expiry cutoffs.")
        st.caption("Revenue, cost, conversion and active users use each mature user's first 30 days (ages 0–29). "
                   "Day-specific retention requires the corresponding follow-up day to be observed.")
        metric_columns = st.columns(6)
        for col, name, field, formatter in zip(metric_columns,
                ["Active users", "Revenue", "Inference cost", "Contribution", "Paid conversion · 30d", "Meaningful D7"],
                ["active_users", "revenue", "inference_cost", "contribution", "paid_conversion", "meaningful_d7"],
                [lambda x: f"{x:,.0f}", money, money, money, percent, percent], strict=True):
            for _, row in summary.iterrows():
                col.metric(f"{name} · {row['variant']}", formatter(row[field]))
        a, b = st.columns([1.05, 1])
        with a:
            st.write("**Return vs meaningful usage**")
            curve = pd.concat([retained.assign(metric="Any activity"),
                               meaningful.assign(metric="Meaningful usage")], ignore_index=True)
            fig = px.line(curve, x="age_day", y="rate", color="variant", line_dash="metric", markers=True,
                          color_discrete_map=COLORS, labels={"age_day": "Day after signup", "rate": "Retention"},
                          hover_data=["eligible", "retained"])
            fig.update_yaxes(tickformat=".0%")
            chart(fig)
        with b:
            st.write("**The cost of engagement**")
            comparison = summary.melt(id_vars="variant", value_vars=["revenue", "inference_cost", "contribution"],
                                      var_name="measure", value_name="USD")
            chart(px.bar(comparison, x="measure", y="USD", color="variant", barmode="group",
                         color_discrete_map=COLORS, labels={"measure": "Mature first-30-day totals"}))
        st.write("**Executive metric table**")
        st.dataframe(variant_table(summary), hide_index=True, use_container_width=True)
        download(summary, "Download filtered metrics", "executive_metrics.csv", "overview_download")
    with cohorts:
        st.subheader("Compare users with the same chance to return.")
        mode = st.radio("Retention definition", ["Meaningful usage", "Any activity"], horizontal=True)
        days = retention(filtered, days=list(range(1, 31)), meaningful=mode == "Meaningful usage")
        fig = px.line(days, x="age_day", y="rate", color="variant", color_discrete_map=COLORS,
                      hover_data=["eligible", "retained"], labels={"rate": "Retention", "age_day": "Day after signup"})
        fig.update_yaxes(tickformat=".0%")
        chart(fig)
        heat = pd.concat([cohort_heatmap(arm_tables(filtered, variant),
                        meaningful=mode == "Meaningful usage").assign(variant=variant)
            for variant in ["control", "treatment"]], ignore_index=True)
        for variant, column in zip(["control", "treatment"], st.columns(2), strict=True):
            with column:
                st.write(f"**{LABELS[variant]}**")
                subset = heat[heat["variant"] == variant] if "variant" in heat.columns else heat
                matrix = subset.pivot_table(index="cohort", columns="age_day", values="rate", aggfunc="first")
                if matrix.empty:
                    st.info("No mature cohorts available.")
                else:
                    fig = go.Figure(go.Heatmap(z=matrix.values, x=matrix.columns, y=matrix.index.astype(str),
                                               zmin=0, zmax=1, colorscale=[[0, "#f1f3ee"], [1, COLORS[variant]]],
                                               hovertemplate="Cohort %{y}<br>Day %{x}<br>Retention %{z:.1%}<extra></extra>",
                                               colorbar={"tickformat": ".0%"}))
                    chart(fig, 320)
        st.caption("Blank cells are censored windows, not zero retention. Cohorts are signup weeks; "
                   "the table below shows each mature denominator.")
        with st.expander("Inspect retention denominators"):
            st.dataframe(days, hide_index=True, use_container_width=True)
        download(heat, "Download cohort analysis", "cohort_retention.csv", "cohort_download")
        series = activity(filtered)
        st.write("**Active user trajectory**")
        measure = st.selectbox("Active user window", ["dau", "wau", "mau", "stickiness"])
        chart(px.line(series, x="date", y=measure, color="variant", color_discrete_map=COLORS))
    with experiment:
        st.subheader("An experiment framework—not a real-world causal claim.")
        st.warning("D7 is sensitive to the unequal credit-expiry schedule: control availability ends at D7, "
                   "later treatment grants at the start of D11. The large model lift partly reflects that design. "
                   "Use post-reward endpoints and a common expiry cutoff to test lasting behavior in a real pilot.")
        st.write("Primary endpoint: meaningful D7 retention. Secondary endpoints are exploratory and "
                 "corrected for multiple comparisons. Population filters are post-hoc views; they are not new confirmatory tests.")
        from src.experimentation.statistics import report

        with st.spinner("Estimating uncertainty and checking randomization…"):
            experiment_report = report(filtered, bootstrap_iterations=300)
        # The native structure preserves interval bounds, p-values, denominator counts and decision checks.
        primary = experiment_report.get("primary", {})
        if primary:
            st.write("**Primary outcome / treatment minus control**")
            cols = st.columns(4)
            cols[0].metric("Control meaningful D7", percent(primary["control_rate"]))
            cols[1].metric("Treatment meaningful D7", percent(primary["treatment_rate"]))
            cols[2].metric("Absolute effect", f"{primary['effect'] * 100:+.2f} pp")
            cols[3].metric("95% confidence interval", f"[{primary['ci_low'] * 100:+.2f}, {primary['ci_high'] * 100:+.2f}] pp")
            effect_rows = [{"metric": "Meaningful D7 · primary", **primary}]
            effect_rows.extend({"metric": key + " · exploratory", **value}
                               for key, value in experiment_report.get("secondary", {}).items())
            effects = pd.DataFrame(effect_rows)
            fig = go.Figure(go.Scatter(x=effects["effect"] * 100, y=effects["metric"], mode="markers",
                           marker={"color": COLORS["treatment"], "size": 9},
                           error_x={"type": "data", "symmetric": False,
                                    "array": (effects["ci_high"] - effects["effect"]) * 100,
                                    "arrayminus": (effects["effect"] - effects["ci_low"]) * 100}))
            fig.add_vline(x=0, line_color="#7b8d87", line_dash="dot")
            fig.update_xaxes(title="Absolute treatment effect (percentage points)")
            chart(fig)
            st.dataframe(effects, hide_index=True, use_container_width=True)
        a, b = st.columns(2)
        with a:
            st.write("**Assignment balance**")
            balance = experiment_report.get("srm", {})
            st.dataframe(pd.DataFrame([{"Arm": "Control", "Assigned users": balance.get("control_n", 0)},
                                       {"Arm": "Treatment", "Assigned users": balance.get("treatment_n", 0)}]),
                         hide_index=True, use_container_width=True)
            st.caption(f"SRM p-value: {balance.get('p_value', float('nan')):.4g} · "
                       f"{'Pass' if balance.get('passed') else 'Investigate'} at α = 0.001")
        with b:
            st.write("**Economic guardrails**")
            economics = experiment_report.get("economics", {})
            st.metric("Contribution effect per mature user", money(economics.get("effect", float("nan"))))
            st.caption(f"95% Welch interval: [{economics.get('ci_low', float('nan')):.2f}, "
                       f"{economics.get('ci_high', float('nan')):.2f}] USD · first 30 days")
            st.caption(f"User-bootstrap sensitivity interval: [{economics.get('bootstrap_low', float('nan')):.2f}, "
                       f"{economics.get('bootstrap_high', float('nan')):.2f}] USD")
        st.write("**Decision under the model**")
        st.write(experiment_report.get("decision", "See the complete report for model decision rules."))
        if experiment_report.get("rules"):
            checks = pd.DataFrame([{"Decision requirement": key.replace("_", " ").capitalize(),
                                    "Status": "Met" if value else "Not met"}
                                   for key, value in experiment_report["rules"].items()])
            st.dataframe(checks, hide_index=True, use_container_width=True)
        plan = experiment_report.get("power", {})
        if plan:
            st.caption(f"Planning assumption: {percent(plan['control_rate'])} baseline, "
                       f"{plan['mde'] * 100:.0f} pp MDE, {percent(plan['power'])} power, "
                       f"α = {plan['alpha']}. Required: {plan['per_arm']:,} mature users per arm. "
                       "The selected population may fall below that requirement.")
        with st.expander("Secondary outcomes, power and complete statistical report"):
            st.json(experiment_report)
        st.download_button("Download experiment report", json.dumps(experiment_report, indent=2, default=str),
                           "experiment_report.json", "application/json")
        st.caption("Confidence intervals quantify sampling uncertainty inside the specified synthetic model. "
                   "They do not account for misspecified behavior or prove an effect in Monolit.")
    with monetization:
        st.subheader("Retention and contribution can move in opposite directions.")
        a, b = st.columns(2)
        with a:
            st.write("**Revenue per user vs inference cost per user**")
            unit = summary.assign(cost_per_user=summary["inference_cost"] / summary["mature_users"].replace(0, float("nan")))
            melted = unit.melt(id_vars="variant", value_vars=["arpu", "cost_per_user"], var_name="Metric", value_name="USD")
            chart(px.bar(melted, x="Metric", y="USD", color="variant", barmode="group", color_discrete_map=COLORS))
        with b:
            st.write("**Meaningful usage vs bonus-only activity**")
            chart(px.scatter(summary, x="meaningful_d7", y="bonus_only_rate", color="variant", size="users",
                             color_discrete_map=COLORS, hover_data=["margin", "paid_conversion"],
                             labels={"meaningful_d7": "Meaningful D7 retention", "bonus_only_rate": "Bonus-only activity share"}))
        user_days = filtered["user_days"]
        grants = filtered["token_transactions"]
        st.write("**Credit accounting**")
        st.caption("Granted credits represent spending entitlement; modeled inference cost is estimated on generated requests. "
                   "Contribution = collected subscription revenue − inference cost. Acquisition, payroll and infrastructure costs are excluded.")
        if "credit_spent" in user_days:
            spend = user_days.merge(filtered["experiment_assignments"][["user_id", "variant"]], on="user_id", how="left") if "variant" not in user_days else user_days
            spending = spend.groupby("variant", as_index=False).agg(credit_spent=("credit_spent", "sum"),
                                                                    requests=("requests", "sum"))
            st.dataframe(variant_table(spending), hide_index=True, use_container_width=True)
        st.dataframe(variant_table(summary[["variant", "users", "paid_conversion", "arpu", "arppu", "inference_cost", "contribution", "margin"]]),
                     hide_index=True, use_container_width=True)
        download(grants, "Download filtered credit ledger", "token_transactions.csv", "credit_download")
    with lab:
        render_lab()
    with external:
        render_external()
    st.divider()
    st.caption("Independent portfolio project by Albina · Business Informatics + Product Analytics · "
               "Real product context informs the question; synthetic data informs only this simulation.")


if __name__ == "__main__":
    main()

