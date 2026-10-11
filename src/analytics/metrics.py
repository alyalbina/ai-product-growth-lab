"""User-weighted metrics. Inactive users remain in eligible denominators."""

import numpy as np
import pandas as pd

VARIANTS = ("control", "treatment")


def filter_tables(tables, user_ids):
    """Subset every user-linked table consistently; preserve standalone metadata."""
    selected = set(user_ids)
    return {
        name: frame[frame.user_id.isin(selected)].copy()
        if isinstance(frame, pd.DataFrame) and "user_id" in frame.columns
        else frame.copy() if hasattr(frame, "copy") else frame
        for name, frame in tables.items()
    }


def retention(tables, days=(1, 7, 30), meaningful=False):
    users, daily = tables["users"], tables["user_days"]
    flag = "is_meaningful" if meaningful else "is_active"
    records = []
    for variant in VARIANTS:
        assigned = users[users.experiment_group == variant]
        for day in days:
            eligible = assigned.loc[assigned.observed_days > day, "user_id"]
            retained = daily.loc[
                daily.user_id.isin(eligible) & (daily.age_day == day) & daily[flag].astype(bool),
                "user_id",
            ].nunique()
            records.append({"variant": variant, "age_day": day, "eligible": len(eligible),
                            "retained": retained, "rate": retained / len(eligible) if len(eligible) else np.nan})
    return pd.DataFrame(records)


def cohort_heatmap(tables, days=(1, 7, 14, 30), meaningful=False):
    users = tables["users"].copy()
    users["cohort"] = pd.to_datetime(users.signup_date).dt.to_period("W").astype(str)
    rows = []
    for cohort, frame in users.groupby("cohort", sort=True):
        view = filter_tables(tables, frame.user_id)
        result = retention(view, days, meaningful)
        for day, group in result.groupby("age_day"):
            eligible, retained = group.eligible.sum(), group.retained.sum()
            rows.append({"cohort": cohort, "age_day": day, "eligible": int(eligible),
                         "rate": retained / eligible if eligible else np.nan})
    return pd.DataFrame(rows, columns=["cohort", "age_day", "eligible", "rate"])


def user_outcomes(tables, horizon=30):
    """One row per assigned user; financial outcomes in ages 0..horizon-1."""
    users = tables["users"].copy()
    daily = tables["user_days"]
    within = daily[daily.age_day.between(0, horizon - 1)]
    totals = within.groupby("user_id").agg(inference_cost=("inference_cost", "sum"),
                                           requests=("requests", "sum"),
                                           active_days=("is_active", "sum"))
    users = users.merge(totals, on="user_id", how="left")
    users[["inference_cost", "requests", "active_days"]] = users[["inference_cost", "requests", "active_days"]].fillna(0)
    payments = tables.get("payments", pd.DataFrame(columns=["user_id", "timestamp", "amount_usd"]))
    if len(payments):
        paid = payments.merge(users[["user_id", "signup_date"]], on="user_id", how="inner")
        ages = (pd.to_datetime(paid.timestamp) - pd.to_datetime(paid.signup_date)).dt.total_seconds() / 86400
        paid = paid[ages.between(0, horizon, inclusive="left")]
        revenue = paid.groupby("user_id").amount_usd.sum()
        users["revenue"] = users.user_id.map(revenue).fillna(0)
    else:
        users["revenue"] = 0.0
    users["paid"] = users.revenue > 0
    users["contribution"] = users.revenue - users.inference_cost
    for day in (1, 7, 30):
        for flag, label in (("is_active", f"d{day}"), ("is_meaningful", f"meaningful_d{day}")):
            retained_ids = daily.loc[(daily.age_day == day) & daily[flag].astype(bool), "user_id"]
            users[label] = users.user_id.isin(retained_ids)
    return users


def summarize(tables):
    """Retention is age-specific; conversion/economics use the mature 30-day ITT set."""
    outcomes = user_outcomes(tables)
    daily = tables["user_days"]
    rows = []
    for variant in VARIANTS:
        all_users = outcomes[outcomes.experiment_group == variant]
        mature = all_users[all_users.observed_days >= 30]
        records = {"variant": variant, "users": len(all_users), "mature_users": len(mature)}
        for day in (1, 7, 30):
            eligible = all_users[all_users.observed_days > day]
            records[f"d{day}"] = eligible[f"d{day}"].mean() if len(eligible) else np.nan
        d7 = all_users[all_users.observed_days > 7]
        records["meaningful_d7"] = d7.meaningful_d7.mean() if len(d7) else np.nan
        revenue, cost = mature.revenue.sum(), mature.inference_cost.sum()
        records.update(paid_conversion=mature.paid.mean() if len(mature) else np.nan,
                       revenue=revenue, inference_cost=cost, contribution=revenue - cost,
                       margin=(revenue - cost) / revenue if revenue else np.nan,
                       arpu=revenue / len(mature) if len(mature) else np.nan,
                       arppu=revenue / mature.paid.sum() if mature.paid.sum() else np.nan,
                       active_users=int((mature.active_days > 0).sum()), requests=int(mature.requests.sum()))
        mature_daily = daily[daily.user_id.isin(mature.user_id) & (daily.age_day < 30)]
        active_count = mature_daily.is_active.sum()
        records["bonus_only_rate"] = mature_daily.bonus_only.sum() / active_count if active_count else np.nan
        rows.append(records)
    return pd.DataFrame(rows)


def activity(tables):
    """Calendar DAU and unique users in inclusive trailing 7/30 calendar days."""
    users, daily = tables["users"], tables["user_days"]
    columns = ["date", "variant", "dau", "wau", "mau", "stickiness"]
    if daily.empty:
        return pd.DataFrame(columns=columns)
    frame = daily.merge(users[["user_id", "experiment_group"]], on="user_id", how="inner")
    frame["date"] = pd.to_datetime(frame.date).dt.normalize()
    calendar = pd.date_range(frame.date.min(), frame.date.max())
    rows = []
    for variant in VARIANTS:
        active = frame[(frame.experiment_group == variant) & frame.is_active.astype(bool)]
        by_day = active.groupby("date").user_id.agg(set).to_dict()
        for date in calendar:
            def unique_in_window(window):
                return len(set().union(*(by_day.get(date - pd.Timedelta(days=i), set()) for i in range(window))))
            dau, wau, mau = len(by_day.get(date, set())), unique_in_window(7), unique_in_window(30)
            rows.append({"date": date.strftime("%Y-%m-%d"), "variant": variant,
                         "dau": dau, "wau": wau, "mau": mau, "stickiness": dau / mau if mau else np.nan})
    return pd.DataFrame(rows, columns=columns)
