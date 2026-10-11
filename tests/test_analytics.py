import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.analytics.database import create_database, run_queries
from src.analytics.metrics import activity, cohort_heatmap, filter_tables, retention, summarize


def fixture_tables():
    users = pd.DataFrame({"user_id": [1, 2, 3, 4], "signup_date": ["2026-01-01"] * 4,
                          "experiment_group": ["control", "control", "treatment", "treatment"],
                          "acquisition_channel": ["organic"] * 4, "observed_days": [31, 31, 8, 2]})
    daily = pd.DataFrame({"user_id": [1, 1, 3, 4], "age_day": [1, 7, 7, 1],
                          "date": ["2026-01-02", "2026-01-08", "2026-01-08", "2026-01-02"],
                          "is_active": [1] * 4, "is_meaningful": [1, 1, 0, 0],
                          "bonus_only": [0, 0, 1, 1], "requests": [2, 2, 0, 0],
                          "inference_cost": [0.5, 0.5, 0, 0], "revenue": [0, 10, 0, 0]})
    return {"users": users, "user_days": daily,
            "payments": pd.DataFrame({"user_id": [1, 1], "timestamp": ["2026-01-08 12:00:00", "2026-02-05 12:00:00"],
                                      "amount_usd": [10.0, 10.0]})}


def test_denominator_includes_users_without_events_and_censors():
    table = retention(fixture_tables()).set_index(["variant", "age_day"])
    assert table.loc[("control", 7), "eligible"] == 2
    assert table.loc[("control", 7), "rate"] == 0.5
    assert table.loc[("treatment", 7), "eligible"] == 1
    assert np.isnan(table.loc[("treatment", 30), "rate"])


def test_meaningful_retention_and_mature_cash_economics():
    summary = summarize(fixture_tables()).set_index("variant")
    assert summary.loc["treatment", "meaningful_d7"] == 0
    assert summary.loc["control", "paid_conversion"] == 0.5
    assert summary.loc["control", "revenue"] == 10
    assert summary.loc["control", "arpu"] == 5
    assert summary.loc["control", "contribution"] == 9
    assert np.isnan(summary.loc["treatment", "arpu"])


def test_empty_filters_all_tables_and_safe_undefined_rates():
    tables = filter_tables(fixture_tables(), [])
    assert all(frame.empty for frame in tables.values())
    assert retention(tables).eligible.sum() == 0
    assert summarize(tables).users.sum() == 0
    assert cohort_heatmap(tables).empty
    assert activity(tables).empty


def test_calendar_activity_unique_users_trailing_windows():
    result = activity(fixture_tables()).set_index(["variant", "date"])
    assert result.loc[("control", "2026-01-08"), "mau"] == 1
    assert result.loc[("control", "2026-01-08"), "wau"] == 1
    assert result.loc[("control", "2026-01-03"), "dau"] == 0
    assert result.loc[("control", "2026-01-03"), "mau"] == 1


def test_no_events_zero_revenue_and_no_payers(tmp_path):
    tables = fixture_tables()
    tables["user_days"] = tables["user_days"].iloc[:0].copy()
    tables["payments"] = tables["payments"].iloc[:0].copy()
    metrics = summarize(tables).set_index("variant")
    assert metrics.loc["control", "d7"] == 0
    assert metrics.loc["control", "paid_conversion"] == 0
    assert metrics.loc["control", "revenue"] == 0
    assert np.isnan(metrics.loc["control", "arppu"])
    assert np.isnan(metrics.loc["control", "margin"])
    path = create_database(tables, tmp_path / "empty-events.db")
    with sqlite3.connect(path) as connection:
        sql = pd.read_sql_query(Path("sql/unit_economics/contribution.sql").read_text(), connection)
    assert sql.iloc[0].revenue == 0
    assert pd.isna(sql.iloc[0].margin)
    assert pd.isna(sql.iloc[0].cost_per_active_user)


def test_sql_retention_matches_python_and_zero_denominator(tmp_path):
    path = create_database(fixture_tables(), tmp_path / "analytics.db")
    query = Path("sql/retention/day_retention.sql").read_text()
    with sqlite3.connect(path) as connection:
        sql = pd.read_sql_query(query, connection)
    py = retention(fixture_tables())
    pd.testing.assert_frame_equal(sql[py.columns], py, check_dtype=False)


def test_sql_economics_does_not_duplicate_payments(tmp_path):
    path = create_database(fixture_tables(), tmp_path / "analytics.db")
    with sqlite3.connect(path) as connection:
        result = pd.read_sql_query(Path("sql/unit_economics/contribution.sql").read_text(), connection)
    assert result.iloc[0].revenue == 10
    assert result.iloc[0].inference_cost == 1
    assert result.iloc[0].users == 2


def test_all_sql_executes_on_simulation(tmp_path):
    from src.simulation.engine import Config, simulate

    tables = simulate(Config(n_users=80, seed=17))
    path = create_database(tables, tmp_path / "simulation.db")
    results = run_queries(path, "sql")
    assert len(results) >= 9
    assert all(isinstance(result, pd.DataFrame) for result in results.values())


def test_ordered_funnel_uses_exact_second_success_not_midnight(tmp_path):
    tables = fixture_tables()
    tables["users"] = tables["users"].iloc[:2].copy()
    rows = []
    for uid in (1, 2):
        for timestamp in ("2026-01-01 10:00:00", "2026-01-01 11:00:00",
                          "2026-01-02 10:00:00", "2026-01-02 15:00:00"):
            rows.append({"request_id": len(rows) + 1, "user_id": uid,
                         "timestamp": timestamp, "success": 1})
    tables["ai_requests"] = pd.DataFrame(rows)
    tables["payments"] = pd.DataFrame({"user_id": [1, 2], "amount_usd": [19, 19],
                                      "timestamp": ["2026-01-02 12:00:00", "2026-01-02 16:00:00"]})
    path = create_database(tables, tmp_path / "ordered-funnel.db")
    with sqlite3.connect(path) as connection:
        result = pd.read_sql_query(Path("sql/funnels/activation_to_paid.sql").read_text(), connection)
    assert result.iloc[0].repeat_usage == 2
    assert result.iloc[0].paid_users == 2
    assert result.iloc[0].repeat_then_paid == 1
