from pathlib import Path

from src.external_analysis import analyze


def test_real_source_integrity():
    result = analyze(Path("data/external/online_shoppers_intention.csv"))
    assert result["sessions"] == 12330
    assert result["purchases"] == 1908
    assert result["missing_cells"] == 0
    assert result["ci_low"] < result["conversion"] < result["ci_high"]
    assert sum(row["sessions"] for row in result["groups"]["VisitorType"]) == 12330
