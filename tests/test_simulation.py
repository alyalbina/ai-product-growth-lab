import numpy as np
import pandas as pd
import pytest

from src.simulation.engine import Config, simulate
from src.validation import assert_valid, validate_tables


@pytest.fixture(scope="module")
def sample():
    return simulate(Config(n_users=120, horizon_days=45, seed=17))


def test_linked_tables_and_money_reconcile(sample):
    assert_valid(sample)
    assert sample["subscriptions"].shape[0] > 0
    assert sample["payments"].shape[0] >= sample["subscriptions"].shape[0]


def test_reproducible_with_same_configuration(sample):
    repeated = simulate(Config(n_users=120, horizon_days=45, seed=17))
    for name, frame in sample.items():
        pd.testing.assert_frame_equal(frame, repeated[name])


def test_observed_windows_are_censored(sample):
    users = sample["users"]
    assert users.observed_days.min() < 30
    assert users.observed_days.max() <= 45
    assert sample["user_days"].shape[0] == users.observed_days.sum()


def test_grants_do_not_require_visit():
    tables = simulate(Config(n_users=120, horizon_days=12, seed=8, return_multiplier=0))
    grants = tables["token_transactions"].query("transaction_type == 'grant'").copy()
    grants["date"] = grants.timestamp.str[:10]
    joined = grants.merge(tables["user_days"], on=["user_id", "date"])
    assert (joined.is_active == 0).any()
    users = tables["users"].query("experiment_group == 'treatment' and observed_days >= 5")
    delivered = grants.groupby("user_id").token_amount.sum()
    # No future eligibility selection: every unpaid treatment member gets day 0..4.
    unpaid = users[~users.user_id.isin(tables["subscriptions"].user_id)]
    assert np.allclose(delivered.reindex(unpaid.user_id), 5.)


def test_expiry_removes_unspent_credit():
    tables = simulate(Config(n_users=30, horizon_days=15, expiry_days=2, return_multiplier=0, purchase_multiplier=0))
    tx = tables["token_transactions"]
    expired = tx.query("transaction_type == 'expiry'")
    assert not expired.empty
    assert (expired.token_amount < 0).all()
    assert (expired.timestamp == expired.expires_at).all()
    assert_valid(tables)


def test_aa_identical_grant_policy():
    tables = simulate(Config(n_users=100, scenario="aa"))
    grants = tables["token_transactions"].query("transaction_type == 'grant'")
    assert len(grants) == 100
    assert (grants.token_amount == 5).all()
    assert (grants.groupby("user_id").size() == 1).all()


def test_cost_multiplier_changes_cost_not_behaviour():
    cheap = simulate(Config(n_users=25, cost_multiplier=1))
    costly = simulate(Config(n_users=25, cost_multiplier=3))
    for field in ["user_id", "timestamp", "success", "credit_spent"]:
        pd.testing.assert_series_equal(cheap["ai_requests"][field], costly["ai_requests"][field])
    assert np.allclose(costly["ai_requests"].estimated_inference_cost, cheap["ai_requests"].estimated_inference_cost * 3, atol=1e-7)


def test_validation_detects_broken_money_and_foreign_key(sample):
    broken = {name: frame.copy(deep=True) for name, frame in sample.items()}
    broken["user_days"].loc[0, "revenue"] += 100
    broken["events"].loc[0, "user_id"] = -1
    errors = validate_tables(broken)
    assert "events: orphan user_id" in errors
    assert "user_days: revenue does not reconcile to source" in errors


@pytest.mark.parametrize("kwargs", [{"n_users": 0}, {"expiry_days": 0}, {"grant_frequency": 0}, {"scenario": "guaranteed_win"}, {"cost_multiplier": -1}, {"subscription_price": float("nan")}])
def test_invalid_config_rejected(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)
