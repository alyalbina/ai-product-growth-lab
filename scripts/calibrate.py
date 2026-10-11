"""Check nominal test behavior and an A/A run of the behavioral engine."""

import json
from pathlib import Path

from src.experimentation.statistics import aa_calibration, experiment_report
from src.simulation.engine import Config, simulate
from scripts.pipeline import json_safe

if __name__ == "__main__":
    calibration = aa_calibration(repetitions=1000, users_per_arm=500)
    behavioral = experiment_report(simulate(Config(n_users=2000, scenario="aa")), bootstrap_iterations=200)
    output = {"inference_calibration": calibration, "behavioral_aa": behavioral,
              "note": "A single behavioral A/A run need not be non-significant. The Monte Carlo test evaluates false-positive frequency under an independent Bernoulli null. Neither validates real instrumentation."}
    path = Path("data/synthetic/aa-calibration.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(output), indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in calibration.items() if k != "p_values"}, indent=2))
