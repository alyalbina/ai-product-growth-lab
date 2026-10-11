"""Independent-user inference. Synthetic evidence does not validate a real policy."""

import math

import numpy as np
from scipy import stats

from src.analytics.metrics import user_outcomes


def wilson(successes, n, alpha=0.05):
    if n < 0 or successes < 0 or successes > n or not 0 < alpha < 1:
        raise ValueError("Valid binomial counts and alpha in (0,1) required")
    if n == 0:
        return (np.nan, np.nan)
    p = successes / n
    z = stats.norm.ppf(1 - alpha / 2)
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, center - radius), min(1.0, center + radius)


wilson_interval = wilson


def binary_comparison(control, treatment, alpha=0.05):
    """Newcombe hybrid-score CI; two-sided pooled score test."""
    c, t = np.asarray(control, dtype=bool), np.asarray(treatment, dtype=bool)
    if not len(c) or not len(t):
        return {"control_n": len(c), "treatment_n": len(t), "control_rate": np.nan,
                "treatment_rate": np.nan, "effect": np.nan, "ci_low": np.nan,
                "ci_high": np.nan, "p_value": np.nan}
    pc, pt = c.mean(), t.mean()
    lc, uc = wilson(c.sum(), len(c), alpha)
    lt, ut = wilson(t.sum(), len(t), alpha)
    effect = pt - pc
    low = effect - math.sqrt((pt - lt) ** 2 + (uc - pc) ** 2)
    high = effect + math.sqrt((ut - pt) ** 2 + (pc - lc) ** 2)
    pooled = (c.sum() + t.sum()) / (len(c) + len(t))
    se = math.sqrt(pooled * (1 - pooled) * (1 / len(c) + 1 / len(t)))
    p = float(2 * stats.norm.sf(abs(effect) / se)) if se else 1.0
    return {"control_n": len(c), "treatment_n": len(t), "control_rate": float(pc),
            "treatment_rate": float(pt), "effect": float(effect), "ci_low": float(low),
            "ci_high": float(high), "p_value": p}


def holm_adjust(p_values):
    """Holm adjustment; undefined tests retain their pre-specified family slots."""
    p = np.asarray(p_values, dtype=float)
    result = np.full(len(p), np.nan)
    valid = np.where(np.isfinite(p))[0]
    order = valid[np.argsort(p[valid])]
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, p[index] * (len(p) - rank)))
        result[index] = running
    return result.tolist()


def contribution_comparison(control, treatment, seed=42, iterations=500):
    """Welch mean CI and bounded user-level percentile bootstrap for skew checks."""
    c, t = np.asarray(control, dtype=float), np.asarray(treatment, dtype=float)
    if len(c) < 2 or len(t) < 2:
        return {"effect": np.nan, "ci_low": np.nan, "ci_high": np.nan, "p_value": np.nan,
                "bootstrap_low": np.nan, "bootstrap_high": np.nan}
    effect = t.mean() - c.mean()
    vc, vt = c.var(ddof=1) / len(c), t.var(ddof=1) / len(t)
    se = math.sqrt(vc + vt)
    denominator = vc**2 / (len(c) - 1) + vt**2 / (len(t) - 1)
    degrees = (vc + vt) ** 2 / denominator if denominator else np.inf
    critical = stats.t.ppf(0.975, degrees)
    p_value = float(2 * stats.t.sf(abs(effect) / se, degrees)) if se else (1.0 if effect == 0 else 0.0)
    rng = np.random.default_rng(seed)
    iterations = max(100, min(1000, int(iterations)))
    samples = np.empty(iterations)
    for i in range(iterations):
        samples[i] = rng.choice(t, len(t), replace=True).mean() - rng.choice(c, len(c), replace=True).mean()
    lo, hi = np.quantile(samples, [0.025, 0.975])
    return {"effect": float(effect), "ci_low": float(effect - critical * se),
            "ci_high": float(effect + critical * se), "p_value": p_value,
            "bootstrap_low": float(lo), "bootstrap_high": float(hi), "bootstrap_iterations": iterations}


def power_plan(control_rate=0.20, mde=0.02, alpha=0.05, power=0.80):
    if not (0 < control_rate < 1 and 0 < control_rate + mde < 1 and mde != 0):
        raise ValueError("Rates must lie inside (0,1) and MDE must be nonzero")
    if not (0 < alpha < 1 and 0.5 < power < 1):
        raise ValueError("Alpha in (0,1) and target power in (0.5,1) required")
    p1, p2 = control_rate, control_rate + mde
    pooled = (p1 + p2) / 2
    z_alpha, z_power = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    n = ((z_alpha * math.sqrt(2 * pooled * (1 - pooled))
          + z_power * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) / mde) ** 2
    return {"control_rate": control_rate, "mde": mde, "alpha": alpha, "power": power,
            "per_arm": math.ceil(n), "total": 2 * math.ceil(n), "method": "two-proportion normal planning approximation"}


def experiment_report(tables, bootstrap_iterations=500):
    users = user_outcomes(tables)
    counts = users.experiment_group.value_counts()
    control_n, treatment_n = int(counts.get("control", 0)), int(counts.get("treatment", 0))
    srm_p = float(stats.chisquare([control_n, treatment_n]).pvalue) if len(users) else np.nan
    srm = {"control_n": control_n, "treatment_n": treatment_n, "p_value": srm_p,
           "passed": bool(np.isfinite(srm_p) and srm_p >= 0.001)}
    def compare(metric, eligible):
        frame = users[eligible]
        return binary_comparison(frame.loc[frame.experiment_group == "control", metric],
                                 frame.loc[frame.experiment_group == "treatment", metric])
    primary = compare("meaningful_d7", users.observed_days > 7)
    secondary = {"d1": compare("d1", users.observed_days > 1),
                 "d7": compare("d7", users.observed_days > 7),
                 "d30": compare("d30", users.observed_days > 30),
                 "paid_conversion": compare("paid", users.observed_days >= 30)}
    for metric, adjusted in zip(secondary.values(), holm_adjust([v["p_value"] for v in secondary.values()])):
        metric["p_adjusted"] = adjusted
    mature = users[users.observed_days >= 30]
    economics = contribution_comparison(mature.loc[mature.experiment_group == "control", "contribution"],
                                        mature.loc[mature.experiment_group == "treatment", "contribution"],
                                        iterations=bootstrap_iterations)
    daily = tables["user_days"]
    mature_daily = daily[daily.user_id.isin(mature.user_id) & (daily.age_day < 30)]
    bonus_rates = {}
    for variant in ("control", "treatment"):
        d = mature_daily[mature_daily.user_id.isin(mature.loc[mature.experiment_group == variant, "user_id"])]
        bonus_rates[variant] = float(d.bonus_only.sum() / d.is_active.sum()) if d.is_active.sum() else np.nan
    bonus_difference = bonus_rates["treatment"] - bonus_rates["control"]
    rules = {"srm": srm["passed"],
             "primary_significant": bool(primary["p_value"] < 0.05 and primary["ci_low"] > 0),
             "practical_effect": bool(primary["effect"] >= 0.02),
             "contribution_noninferior": bool(economics["ci_low"] >= -0.25),
             "paid_conversion_noninferior": bool(secondary["paid_conversion"]["ci_low"] >= -0.01),
             "bonus_only_guardrail": bool(bonus_difference <= 0.10)}
    if not srm["passed"]:
        decision = "Investigate assignment integrity"
    elif all(rules.values()):
        decision = "Advance to a real controlled pilot"
    elif economics["ci_high"] < -0.25 or secondary["paid_conversion"]["ci_high"] < -0.01:
        decision = "Do not advance: economic guardrail harm"
    else:
        decision = "Inconclusive: refine assumptions and collect evidence"
    return {"primary": primary, "secondary": secondary, "srm": srm, "economics": economics,
            "bonus_only_difference": bonus_difference, "rules": rules, "decision": decision,
            "power": power_plan(), "data_type": "Synthetic analytical simulation"}


report = experiment_report


def aa_calibration(seed=42, repetitions=1000, users_per_arm=500, null_rate=0.20):
    """Bernoulli-null test calibration; separate from behavioral model validation."""
    if repetitions < 1 or users_per_arm < 1 or not 0 < null_rate < 1:
        raise ValueError("Positive repetitions/arm size and rate in (0,1) required")
    if repetitions > 10000 or users_per_arm > 100000:
        raise ValueError("Calibration workload exceeds the supported cap")
    rng = np.random.default_rng(seed)
    c = rng.binomial(users_per_arm, null_rate, repetitions)
    t = rng.binomial(users_per_arm, null_rate, repetitions)
    pooled = (c + t) / (2 * users_per_arm)
    se = np.sqrt(pooled * (1 - pooled) * 2 / users_per_arm)
    z = np.divide((t - c) / users_per_arm, se, out=np.zeros(repetitions), where=se > 0)
    p = 2 * stats.norm.sf(np.abs(z))
    rejected = int((p < 0.05).sum())
    low, high = wilson(rejected, repetitions)
    return {"seed": seed, "repetitions": repetitions, "users_per_arm": users_per_arm,
            "false_positive_rate": rejected / repetitions, "ci_low": float(low), "ci_high": float(high),
            "p_values": p.tolist(), "interpretation": "Monte Carlo calibration under an independent Bernoulli null; not real experiment evidence."}
