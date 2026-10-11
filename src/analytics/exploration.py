"""Reproducible descriptive diagnostics without post-treatment segmentation."""

import pandas as pd

from .metrics import filter_tables, summarize, user_outcomes


def data_profile(tables):
    """Size, missingness and exact-row duplicates for every physical table."""
    rows = []
    for name, frame in tables.items():
        if not isinstance(frame, pd.DataFrame):
            continue
        rows.append({"table": name, "rows": len(frame), "columns": len(frame.columns),
                     "missing_cells": int(frame.isna().sum().sum()),
                     "duplicate_rows": int(frame.duplicated().sum())})
    return pd.DataFrame(rows)


def segment_profitability(tables, dimension="user_segment"):
    """Descriptive presignup segments; all-variant ITT metrics per segment."""
    if dimension not in {"user_segment", "acquisition_channel", "country"}:
        raise ValueError("Use a presignup segment, channel or country")
    pieces = []
    for segment, users in tables["users"].groupby(dimension):
        metrics = summarize(filter_tables(tables, users.user_id))
        metrics.insert(0, dimension, segment)
        pieces.append(metrics)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def engagement_distribution(tables):
    """One row per mature user; includes zero-engagement and zero-revenue users."""
    users = user_outcomes(tables)
    users = users[users.observed_days >= 30]
    return users[["user_id", "experiment_group", "user_segment", "acquisition_channel",
                  "active_days", "requests", "revenue", "inference_cost", "contribution", "paid"]].copy()
