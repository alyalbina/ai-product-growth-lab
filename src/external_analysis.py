"""Independent descriptive analysis of licensed UCI e-commerce sessions."""

import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

import pandas as pd

from src.experimentation.statistics import wilson_interval

SOURCE = "https://archive.ics.uci.edu/static/public/468/online+shoppers+purchasing+intention+dataset.zip"
DATASET = "https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset"


def fetch(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SOURCE, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    path = destination / "online_shoppers_intention.csv"
    path.write_bytes(archive.read("online_shoppers_intention.csv"))
    return path


def analyze(path: Path) -> dict:
    frame = pd.read_csv(path)
    required = {"Revenue", "VisitorType", "Month", "TrafficType", "ProductRelated"}
    if not required.issubset(frame.columns):
        raise ValueError("UCI source schema changed")
    if not frame.Revenue.isin([True, False]).all():
        raise ValueError("Revenue must be a purchase indicator, not monetary revenue")
    # Identical vectors have no identity key. Keep them, report them, do not
    # equate identical measurements with confirmed duplicate sessions.
    duplicates = int(frame.duplicated().sum())
    groups = {}
    for field in ["VisitorType", "Month", "TrafficType", "Weekend"]:
        rows = []
        for key, subset in frame.groupby(field, observed=True):
            n, k = len(subset), int(subset.Revenue.sum())
            low, high = wilson_interval(k, n)
            rows.append({"group": str(key), "sessions": n, "purchases": k,
                         "conversion": k / n, "ci_low": low, "ci_high": high})
        groups[field] = rows
    n, k = len(frame), int(frame.Revenue.sum())
    low, high = wilson_interval(k, n)
    return {
        "source": DATASET, "doi": "10.24432/C5F88Q", "license": "CC BY 4.0",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sessions": n, "purchases": k, "conversion": k / n,
        "ci_low": low, "ci_high": high, "missing_cells": int(frame.isna().sum().sum()),
        "identical_feature_rows": duplicates,
        "numeric_outliers": {c: {"min": float(frame[c].min()), "max": float(frame[c].max()),
                                    "p99": float(frame[c].quantile(.99))}
                             for c in ["ProductRelated", "ProductRelated_Duration", "BounceRates", "ExitRates"]},
        "groups": groups,
        "interpretation": "Descriptive session conversion. Associations are not causal. No user history, exact dates or monetary revenue; retention and ARPU cannot be estimated. PageValues is outcome-related and unsuitable for a pre-treatment causal adjustment.",
    }


def save_analysis(folder: Path) -> dict:
    path = folder / "online_shoppers_intention.csv"
    if not path.exists():
        fetch(folder)
    result = analyze(path)
    (folder / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
