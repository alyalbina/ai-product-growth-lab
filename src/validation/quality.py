"""Validate foreign keys, observation windows and monetary reconciliation."""

import numpy as np
import pandas as pd

from src.simulation.engine import SCHEMAS


def validate_tables(tables: dict[str, pd.DataFrame]) -> list[str]:
    """Return actionable errors (empty list means all checks passed)."""
    errors = []
    for name, columns in SCHEMAS.items():
        if name not in tables:
            errors.append(f"missing table {name}")
        elif missing := set(columns) - set(tables[name].columns):
            errors.append(f"{name}: missing columns {sorted(missing)}")
    if errors:
        return errors
    users = tables["users"]
    uids = set(users.user_id)
    keys = {"users": "user_id", "events": "event_id", "token_transactions": "transaction_id", "subscriptions": "subscription_id", "ai_requests": "request_id", "experiment_assignments": "user_id", "payments": "payment_id"}
    for name, frame in tables.items():
        if name not in SCHEMAS:
            continue
        if name in keys and (frame[keys[name]].isna().any() or frame[keys[name]].duplicated().any()):
            errors.append(f"{name}: duplicate or null primary key")
        if not set(frame.user_id).issubset(uids):
            errors.append(f"{name}: orphan user_id")
    if users.empty:
        return errors
    assignments = tables["experiment_assignments"]
    if set(assignments.user_id) != uids:
        errors.append("experiment_assignments: not exactly one assignment per user")
    joined = assignments.merge(users[["user_id", "experiment_group", "signup_date"]], on="user_id")
    if not joined.variant.eq(joined.experiment_group).all() or not joined.assigned_at.eq(joined.signup_date).all():
        errors.append("experiment_assignments: inconsistent arm or assignment time")
    if not users.experiment_group.isin(["control", "treatment"]).all():
        errors.append("users: invalid experiment group")
    if (users.observed_days < 1).any():
        errors.append("users: invalid observed_days")
    for name, field in {"events": "event_timestamp", "token_transactions": "timestamp", "ai_requests": "timestamp", "subscriptions": "started_at", "payments": "timestamp"}.items():
        merged = tables[name].merge(users[["user_id", "signup_date", "observed_days"]], on="user_id")
        times = pd.to_datetime(merged[field], errors="coerce")
        signup = pd.to_datetime(merged.signup_date)
        end = signup + pd.to_timedelta(merged.observed_days, unit="D")
        if times.isna().any() or ((times < signup) | (times >= end)).any():
            errors.append(f"{name}: timestamp outside observation window")
    days = tables["user_days"]
    if days.duplicated(["user_id", "age_day"]).any():
        errors.append("user_days: duplicate user age day")
    counts = days.groupby("user_id").size().reindex(users.user_id, fill_value=0)
    if not np.array_equal(counts.to_numpy(), users.observed_days.to_numpy()):
        errors.append("user_days: missing observed days")
    expected_days = days.merge(users[["user_id", "signup_date", "observed_days"]], on="user_id")
    expected_date = pd.to_datetime(expected_days.signup_date) + pd.to_timedelta(expected_days.age_day, unit="D")
    if not pd.to_datetime(expected_days.date).eq(expected_date).all() or ((expected_days.age_day < 0) | (expected_days.age_day >= expected_days.observed_days)).any():
        errors.append("user_days: inconsistent age/date")
    if not days.is_meaningful.eq((days.requests >= 2).astype(int)).all():
        errors.append("user_days: inconsistent meaningful activity")
    if not days.bonus_only.eq(((days.is_active == 1) & (days.requests == 0)).astype(int)).all():
        errors.append("user_days: inconsistent bonus-only activity")
    if ((days.is_active == 0) & (days.requests > 0)).any():
        errors.append("user_days: requests on inactive days")
    requests = tables["ai_requests"]
    ledger = tables["token_transactions"]
    payments = tables["payments"]
    subscriptions = tables["subscriptions"]
    if not set(payments.subscription_id).issubset(set(subscriptions.subscription_id)):
        errors.append("payments: orphan subscription_id")
    if not payments.empty:
        linked_payments = payments.merge(subscriptions[["subscription_id", "user_id", "amount_usd"]], on="subscription_id", suffixes=("", "_sub"))
        if not linked_payments.user_id.eq(linked_payments.user_id_sub).all() or not np.allclose(linked_payments.amount_usd, linked_payments.amount_usd_sub):
            errors.append("payments: inconsistent invoice owner or amount")
    if not subscriptions.empty:
        cancellations = subscriptions.dropna(subset=["cancelled_at"])
        if (pd.to_datetime(cancellations.cancelled_at) < pd.to_datetime(cancellations.started_at)).any():
            errors.append("subscriptions: cancellation precedes start")
    for frame, columns, name in [(requests, ["estimated_inference_cost", "credit_spent", "input_tokens", "output_tokens"], "ai_requests"), (payments, ["amount_usd"], "payments"), (days, ["revenue", "inference_cost", "credit_spent"], "user_days")]:
        if not np.isfinite(frame[columns].to_numpy(dtype=float)).all() or (frame[columns] < 0).any().any():
            errors.append(f"{name}: nonfinite or negative financial/usage value")
    if not requests.success.isin([0, 1]).all() or ((requests.success == 0) & (requests.credit_spent > 0)).any():
        errors.append("ai_requests: invalid success or charged failed request")
    if not ledger.transaction_type.isin(["grant", "debit", "expiry"]).all():
        errors.append("token_transactions: invalid transaction type")
    if ((ledger.transaction_type == "grant") & (ledger.token_amount <= 0)).any() or ((ledger.transaction_type != "grant") & (ledger.token_amount > 0)).any():
        errors.append("token_transactions: incorrect signed amount")
    if (ledger.balance_after < -1e-7).any():
        errors.append("token_transactions: negative credit balance")
    ordered = ledger.sort_values(["user_id", "transaction_id"])
    if not np.allclose(ordered.groupby("user_id").token_amount.cumsum(), ordered.balance_after, atol=1e-6):
        errors.append("token_transactions: running balance does not reconcile")
    grants = ledger[ledger.transaction_type == "grant"]
    if not set(ledger.grant_id).issubset(set(grants.transaction_id)):
        errors.append("token_transactions: orphan grant_id")
    if not ledger.empty:
        lot_check = ledger.merge(grants[["transaction_id", "user_id", "token_amount", "expires_at"]], left_on="grant_id", right_on="transaction_id", suffixes=("", "_grant"))
        if not lot_check.user_id.eq(lot_check.user_id_grant).all():
            errors.append("token_transactions: grant belongs to another user")
        lot_balance = ledger.groupby("grant_id").token_amount.sum()
        if (lot_balance < -1e-6).any():
            errors.append("token_transactions: lot overspent")
        used = lot_check[lot_check.transaction_type == "debit"]
        if (pd.to_datetime(used.timestamp) >= pd.to_datetime(used.expires_at_grant)).any():
            errors.append("token_transactions: spent expired credit")
        expired = lot_check[lot_check.transaction_type == "expiry"]
        if not expired.timestamp.eq(expired.expires_at_grant).all():
            errors.append("token_transactions: incorrect expiry time")
    debit = ledger[ledger.transaction_type == "debit"]
    if not set(debit.request_id.dropna()).issubset(set(requests.request_id)):
        errors.append("token_transactions: orphan request_id")
    debit_owners = debit.merge(requests[["request_id", "user_id"]], on="request_id", suffixes=("", "_request"))
    if not debit_owners.user_id.eq(debit_owners.user_id_request).all():
        errors.append("token_transactions: request belongs to another user")
    request_debit = debit.groupby("request_id").token_amount.sum().mul(-1).reindex(requests.request_id, fill_value=0)
    if not np.allclose(request_debit.to_numpy(), requests.credit_spent.to_numpy(), atol=1e-6):
        errors.append("token_transactions: request debits do not reconcile")
    for source, value, expected, aggregation in [(requests, "estimated_inference_cost", "inference_cost", "sum"), (requests, "credit_spent", "credit_spent", "sum"), (requests, "success", "requests", "sum"), (payments, "amount_usd", "revenue", "sum")]:
        source = source.copy()
        source["date"] = source.timestamp.str[:10]
        actual = source.groupby(["user_id", "date"])[value].agg(aggregation)
        expected_frame = days.set_index(["user_id", "date"])[expected]
        if not np.allclose(actual.reindex(expected_frame.index, fill_value=0), expected_frame, atol=1e-6):
            errors.append(f"user_days: {expected} does not reconcile to source")
    return errors


def assert_valid(tables: dict[str, pd.DataFrame]) -> None:
    """Raise ValueError when the generated tables violate their contract."""
    errors = validate_tables(tables)
    if errors:
        raise ValueError("Data quality checks failed: " + "; ".join(errors))
