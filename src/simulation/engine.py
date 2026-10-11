"""A daily, forward-only user model with an auditable retail-credit ledger."""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import math

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Config:
    n_users: int = 10_000
    horizon_days: int = 90
    seed: int = 42
    scenario: str = "neutral"
    daily_credit: float = 1.0
    grant_days: int = 5
    grant_frequency: int = 1
    expiry_days: int = 7
    cost_multiplier: float = 1.0
    subscription_price: float = 19.0
    return_multiplier: float = 1.0
    purchase_multiplier: float = 1.0

    def __post_init__(self):
        if self.scenario not in {"positive", "neutral", "negative", "aa"}:
            raise ValueError("scenario must be positive, neutral, negative or aa")
        for name in ("n_users", "horizon_days", "grant_days", "grant_frequency", "expiry_days"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("daily_credit", "cost_multiplier", "subscription_price", "return_multiplier", "purchase_multiplier"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")


SCHEMAS = {
    "users": ["user_id", "signup_date", "acquisition_channel", "user_segment", "country", "experiment_group", "observed_days"],
    "events": ["event_id", "user_id", "event_timestamp", "event_type", "session_id"],
    "token_transactions": ["transaction_id", "user_id", "timestamp", "transaction_type", "token_amount", "estimated_cost_usd", "balance_after", "grant_id", "expires_at", "request_id"],
    "subscriptions": ["subscription_id", "user_id", "plan", "started_at", "cancelled_at", "amount_usd"],
    "ai_requests": ["request_id", "user_id", "timestamp", "model_type", "input_tokens", "output_tokens", "estimated_inference_cost", "success", "session_id", "credit_spent"],
    "experiment_assignments": ["user_id", "variant", "assigned_at"],
    "payments": ["payment_id", "user_id", "subscription_id", "timestamp", "amount_usd", "payment_type"],
    "user_days": ["user_id", "date", "age_day", "is_active", "is_meaningful", "requests", "inference_cost", "revenue", "credit_spent", "bonus_only"],
}


def simulate(config: Config | None = None) -> dict[str, pd.DataFrame]:
    """Return linked tables. Dates are UTC-naive ISO strings for SQLite.

    A request is successful only if funded and the service succeeds. AI requests
    include failures; user_days.requests counts successes. Treatment assignment
    does not affect A/A paths. No outcome is forced or calibrated after simulation.
    """
    cfg = config or Config()
    rows = {name: [] for name in SCHEMAS}
    rng = np.random.default_rng(cfg.seed)
    start = datetime(2025, 1, 1)
    signup_offsets = rng.integers(0, cfg.horizon_days, cfg.n_users)
    variants = rng.choice(["control", "treatment"], cfg.n_users)
    channels = rng.choice(["organic", "paid_search", "referral", "social"], cfg.n_users, p=[.35, .25, .25, .15])
    countries = rng.choice(["AE", "US", "GB", "DE", "IN"], cfg.n_users, p=[.2, .25, .15, .15, .25])
    scenario = {
        "positive": {"reward": .16, "learning": .055, "buy": 1.20, "waste": .07},
        "neutral": {"reward": .12, "learning": .012, "buy": .95, "waste": .16},
        "negative": {"reward": .24, "learning": -.012, "buy": .65, "waste": .39},
        "aa": {"reward": 0., "learning": 0., "buy": 1., "waste": 0.},
    }[cfg.scenario]

    def stamp(day, seconds=0):
        return (start + timedelta(days=int(day), seconds=int(seconds))).isoformat(sep=" ")

    def event(uid, day, kind, session=None, seconds=0):
        rows["events"].append((len(rows["events"]) + 1, uid, stamp(day, seconds), kind, session))

    for index in range(cfg.n_users):
        uid = index + 1
        signup = int(signup_offsets[index])
        group = str(variants[index])
        channel = str(channels[index])
        # Acquisition selects a distribution; assignment is independent of it.
        probs = {"organic": [.40, .42, .18], "paid_search": [.25, .40, .35], "referral": [.50, .40, .10], "social": [.18, .32, .50]}[channel]
        segment = str(rng.choice(["professional", "explorer", "casual"], p=probs))
        base_value = {"professional": .78, "explorer": .49, "casual": .22}[segment]
        value = float(np.clip(rng.normal(base_value, .12), .05, .97))
        intensity = {"professional": 4.2, "explorer": 2.6, "casual": 1.2}[segment]
        budget = float(rng.lognormal(0, .35))
        observed = cfg.horizon_days - signup
        rows["users"].append((uid, stamp(signup), channel, segment, str(countries[index]), group, observed))
        rows["experiment_assignments"].append((uid, group, stamp(signup)))
        event(uid, signup, "signup")
        daily_arm = group == "treatment" and cfg.scenario != "aa"
        lots = []  # [grant_id, remaining credit dollars, absolute expiry day]
        balance = 0.
        sub_id = None
        next_renewal = None
        ever_paid = False
        meaningful_days = 0
        last_active_age = None

        def ledger(day, kind, amount, grant_id=None, expiry=None, request_id=None, inference=0., seconds=0):
            nonlocal balance
            balance = round(balance + amount, 8)
            if abs(balance) < 1e-7:
                balance = 0.
            tid = len(rows["token_transactions"]) + 1
            rows["token_transactions"].append((tid, uid, stamp(day, seconds), kind, round(amount, 8), inference, balance, grant_id or tid, stamp(expiry) if expiry is not None else None, request_id))
            return tid

        for age in range(observed):
            day = signup + age
            day_cost = day_revenue = spent = 0.
            successes = 0
            # Expiry and entitlement run independently of a login.
            for lot in lots:
                if lot[2] <= day and lot[1] > 1e-7:
                    ledger(day, "expiry", -lot[1], lot[0], lot[2])
                    lot[1] = 0.
            if sub_id is not None and day == next_renewal:
                cancel_p = .10 + .25 * (1 - value)
                if rng.random() < cancel_p:
                    rows["subscriptions"][sub_id - 1][4] = stamp(day, 10)
                    event(uid, day, "subscription_cancelled", seconds=10)
                    sub_id = None
                    next_renewal = None
                else:
                    rows["payments"].append((len(rows["payments"]) + 1, uid, sub_id, stamp(day, 10), cfg.subscription_price, "renewal"))
                    day_revenue += cfg.subscription_price
                    next_renewal += 30
                    event(uid, day, "subscription_renewed", seconds=10)
            eligible = (age % cfg.grant_frequency == 0 and age // cfg.grant_frequency < cfg.grant_days) if daily_arm else age == 0
            granted_today = False
            if eligible and sub_id is None:
                amount = cfg.daily_credit if daily_arm else 5.
                if amount > 0:
                    grant_id = ledger(day, "grant", amount, expiry=day + cfg.expiry_days, seconds=20)
                    lots.append([grant_id, amount, day + cfg.expiry_days])
                    event(uid, day, "token_grant", seconds=20)
                    granted_today = True
            # All explanatory state is from the past or current day's policy.
            novelty = math.exp(-age / 5)
            habit = min(meaningful_days / 14, 1)
            p_active = .045 + .38 * value + .12 * habit
            p_active *= .55 + .45 * math.exp(-age / 45)
            if balance <= 0 and sub_id is None:
                p_active *= .45
            if sub_id is not None:
                p_active += .16
            if last_active_age is not None and age - last_active_age > 14:
                p_active *= .65
            if daily_arm:
                p_active += scenario["reward"] * novelty * (1 if granted_today else .2)
            p_active *= 1 + .07 * math.cos(2 * math.pi * (day % 7) / 7)
            p_active *= cfg.return_multiplier
            active = age == 0 or rng.random() < np.clip(p_active, 0, .95)
            if active:
                last_active_age = age
                session = f"s{uid}_{age}"
                event(uid, day, "session_start", session, 3600)
                bonus_hunter = daily_arm and rng.random() < scenario["waste"] * novelty
                attempts = 0 if bonus_hunter else int(rng.poisson(intensity * (.65 + value))) + 1
                for attempt in range(attempts):
                    seconds = 3700 + attempt * 90
                    # Purchase is a behavioral response to value and credit friction.
                    premium = rng.random() < .20 + .30 * value
                    retail_cost = .32 if premium else .12
                    if sub_id is None and balance + 1e-7 < retail_cost and not ever_paid:
                        p_buy = .015 + .08 * value + .04 * min(meaningful_days / 5, 1)
                        p_buy *= budget * cfg.purchase_multiplier
                        p_buy *= math.exp(-cfg.subscription_price / 38)
                        if daily_arm:
                            p_buy *= scenario["buy"]
                        if rng.random() < min(p_buy, .70):
                            sub_id = len(rows["subscriptions"]) + 1
                            rows["subscriptions"].append([sub_id, uid, "pro_monthly", stamp(day, seconds), None, cfg.subscription_price])
                            rows["payments"].append((len(rows["payments"]) + 1, uid, sub_id, stamp(day, seconds), cfg.subscription_price, "initial"))
                            day_revenue += cfg.subscription_price
                            next_renewal = day + 30
                            ever_paid = True
                            event(uid, day, "subscription_started", session, seconds)
                    funded = sub_id is not None or balance + 1e-7 >= retail_cost
                    if not funded:
                        # One failed attempt provides observable depletion friction.
                        request_id = len(rows["ai_requests"]) + 1
                        rows["ai_requests"].append((request_id, uid, stamp(day, seconds + 1), "premium" if premium else "standard", 0, 0, 0., 0, session, 0.))
                        event(uid, day, "ai_request_failed", session, seconds + 1)
                        break
                    input_tokens = int(rng.integers(150, 1200))
                    output_tokens = int(rng.integers(100, 900))
                    # Synthetic marginal cost schedule, not a vendor price quote.
                    inference = round((input_tokens * .000003 + output_tokens * .000012) * (2.4 if premium else 1) * cfg.cost_multiplier, 8)
                    success = int(rng.random() < .975)
                    charged = retail_cost if success and sub_id is None else 0.
                    request_id = len(rows["ai_requests"]) + 1
                    rows["ai_requests"].append((request_id, uid, stamp(day, seconds + 1), "premium" if premium else "standard", input_tokens, output_tokens, inference, success, session, charged))
                    if charged:
                        left = charged
                        for lot in lots:
                            take = min(lot[1], left)
                            if take > 1e-7:
                                ledger(day, "debit", -take, lot[0], lot[2], request_id, inference=round(inference * take / charged, 8), seconds=seconds + 1)
                                lot[1] = round(lot[1] - take, 8)
                                left = round(left - take, 8)
                            if left <= 1e-7:
                                break
                    successes += success
                    spent += charged
                    day_cost += inference
                    event(uid, day, "ai_request" if success else "ai_request_failed", session, seconds + 1)
                if successes >= 2:
                    meaningful_days += 1
                    if daily_arm:
                        value = float(np.clip(value + scenario["learning"] * novelty, .05, .97))
                    event(uid, day, "activation" if meaningful_days == 1 else "meaningful_usage", session, 6000)
            rows["user_days"].append((uid, stamp(day)[:10], age, int(active), int(successes >= 2), successes, round(day_cost, 8), round(day_revenue, 8), round(spent, 8), int(active and successes == 0)))

    result = {name: pd.DataFrame(data, columns=SCHEMAS[name]) for name, data in rows.items()}
    for frame in result.values():
        frame.attrs["synthetic"] = True
        frame.attrs["config"] = asdict(cfg)
    return result
