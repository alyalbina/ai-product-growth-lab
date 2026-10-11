"""Build a reproducible data release and execute every SQL analysis."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from src.analytics.metrics import summarize
from src.analytics.database import create_database, run_queries
from src.experimentation.statistics import experiment_report
from src.simulation.engine import Config, simulate
from src.validation.quality import validate_tables


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return value


def build(config: Config, folder: Path, scenarios=False):
    started = time.perf_counter()
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Simulating {config.n_users:,} users / {config.horizon_days} calendar days", flush=True)
    tables = simulate(config)
    errors = validate_tables(tables)
    if errors:
        raise ValueError("Data validation failed: " + "; ".join(errors))
    manifest = {"config": asdict(config), "tables": {}, "data_origin": "synthetic"}
    for name, frame in tables.items():
        path = folder / f"{name}.csv.gz"
        # Fixed gzip mtime makes hashes stable between runs.
        frame.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
        manifest["tables"][name] = {"rows": len(frame), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    db = folder / "growth_lab.sqlite"
    create_database(tables, db)
    sql_results = run_queries(db, Path("sql"))
    sql_folder = folder / "sql-results"
    sql_folder.mkdir(exist_ok=True)
    for name, frame in sql_results.items():
        frame.to_csv(sql_folder / (name.replace("/", "__") + ".csv"), index=False)
    report = {"config": asdict(config), "summary": summarize(tables).to_dict("records"),
              "experiment": experiment_report(tables), "validation_errors": errors,
              "sql_queries_executed": list(sql_results), "scenario_comparison": []}
    if scenarios:
        for scenario in ["positive", "neutral", "negative"]:
            scenario_config = Config(**{**asdict(config), "scenario": scenario})
            alternative = tables if scenario == config.scenario else simulate(scenario_config)
            if issues := validate_tables(alternative):
                raise ValueError(issues)
            report["scenario_comparison"].append({"scenario": scenario,
                "summary": summarize(alternative).to_dict("records"),
                "experiment": experiment_report(alternative, bootstrap_iterations=200)})
            print(f"Scenario {scenario} analyzed", flush=True)
    (folder / "manifest.json").write_text(json.dumps(json_safe(manifest), indent=2), encoding="utf-8")
    (folder / "report.json").write_text(json.dumps(json_safe(report), indent=2, allow_nan=False), encoding="utf-8")
    print(f"Validated release + {len(sql_results)} SQL queries in {time.perf_counter()-started:.1f}s", flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scenario", choices=["positive", "neutral", "negative", "aa"], default="neutral")
    parser.add_argument("--scenarios", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("data/synthetic"))
    args = parser.parse_args()
    build(Config(n_users=args.users, seed=args.seed, scenario=args.scenario), args.output, args.scenarios)
