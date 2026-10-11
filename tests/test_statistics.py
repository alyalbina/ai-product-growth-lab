import numpy as np
import pytest

from src.experimentation.statistics import (
    aa_calibration,
    binary_comparison,
    contribution_comparison,
    holm_adjust,
    power_plan,
    wilson,
)


def test_binary_comparison_sign_symmetry_and_boundary_intervals():
    c, t = [False] * 100, [True] * 100
    result = binary_comparison(c, t)
    swapped = binary_comparison(t, c)
    assert result["effect"] == 1
    assert 0 < result["ci_low"] < result["ci_high"] <= 1
    assert result["ci_low"] == pytest.approx(-swapped["ci_high"])
    assert result["p_value"] == swapped["p_value"]
    assert binary_comparison(c, c)["p_value"] == 1


def test_empty_binary_returns_unknown_not_zero():
    result = binary_comparison([], [True])
    assert np.isnan(result["p_value"])
    assert np.isnan(result["effect"])
    assert np.isnan(wilson(0, 0)[0])


def test_holm_monotone_and_nan_preserved():
    result = holm_adjust([0.01, 0.04, 0.03, np.nan])
    assert result[:3] == pytest.approx([0.04, 0.09, 0.09])
    assert np.isnan(result[3])


def test_contribution_bootstrap_reproducible_and_constants():
    c, t = np.arange(20), np.arange(20) + 1
    assert contribution_comparison(c, t, iterations=100) == contribution_comparison(c, t, iterations=100)
    constant = contribution_comparison(np.zeros(10), np.zeros(10), iterations=100)
    assert constant["effect"] == 0
    assert constant["ci_low"] == 0
    assert constant["p_value"] == 1


def test_power_planning_and_aa_null_calibration():
    result = power_plan()
    assert 6400 < result["per_arm"] < 6600
    calibration = aa_calibration(repetitions=2000)
    assert 0.03 < calibration["false_positive_rate"] < 0.07
    assert calibration["ci_low"] < 0.05 < calibration["ci_high"]
    with pytest.raises(ValueError):
        power_plan(mde=0)


def test_srm_uses_all_assigned_not_only_metric_eligible():
    from tests.test_analytics import fixture_tables
    from src.experimentation.statistics import experiment_report

    result = experiment_report(fixture_tables(), bootstrap_iterations=100)
    assert result["srm"]["control_n"] == 2
    assert result["srm"]["treatment_n"] == 2
    assert result["primary"]["treatment_n"] == 1
    assert not result["rules"]["contribution_noninferior"]
