"""One-factor perturbations. Model response, not real causal policy effects."""

from dataclasses import asdict
import argparse
import json
from pathlib import Path

import pandas as pd

from src.analytics.metrics import summarize
from src.simulation.engine import Config, simulate

GRID = {
    "daily_credit": [.5, 1., 1.5],
    "grant_frequency": [1, 2, 3],
    "cost_multiplier": [.5, 1., 2.],
    "subscription_price": [9., 19., 29.],
    "return_multiplier": [.8, 1., 1.2],
    "purchase_multiplier": [.6, 1., 1.4],
    "expiry_days": [1, 7, 30],
}


def run(n_users=1000, seeds=(42, 43, 44)):
    rows = []
    for parameter, values in GRID.items():
        for value in values:
            for seed in seeds:
                config = Config(n_users=n_users, seed=seed, **{parameter: value})
                summary = summarize(simulate(config)).set_index("variant")
                control, treatment = summary.loc["control"], summary.loc["treatment"]
                rows.append({"parameter": parameter, "value": value, "seed": seed,
                             "users": n_users, "meaningful_d7_effect": treatment.meaningful_d7-control.meaningful_d7,
                             "paid_conversion_effect": treatment.paid_conversion-control.paid_conversion,
                             "contribution_per_user_effect": treatment.contribution/treatment.mature_users-control.contribution/control.mature_users,
                             "control_margin": control.margin, "treatment_margin": treatment.margin,
                             "treatment_credit_entitlement": config.daily_credit*config.grant_days,
                             "config": json.dumps(asdict(config), sort_keys=True)})
            print(f"Completed {parameter}={value}", flush=True)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=1000)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    args = parser.parse_args()
    destination = Path("data/synthetic/sensitivity.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)
    run(args.users, args.seeds).to_csv(destination, index=False)
