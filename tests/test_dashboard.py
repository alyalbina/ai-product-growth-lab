"""UI regressions: full render, a zero-user selection and a real lab recalculation."""

from dataclasses import replace
from pathlib import Path

import pytest

st = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402
from src.simulation.engine import simulate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app(monkeypatch, tmp_path):
    # Small linked data retain mature/immature cohorts and every integration path.
    # Hide generated CSVs so the same test also runs after the full pipeline.
    st.cache_data.clear()
    original_exists = Path.exists

    def exists(path):
        if path.parent == ROOT / "data" / "synthetic" and path.suffix in {".csv", ".gz"}:
            return False
        return original_exists(path)

    monkeypatch.setattr(Path, "exists", exists)
    monkeypatch.setattr("src.simulation.engine.simulate",
                        lambda config: simulate(replace(config, n_users=120)))
    return AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=60)


def test_all_analytical_tabs_render(app):
    app.run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Overview", "Cohorts", "Experiment", "Monetization", "Simulation lab", "External real data"
    ]
    assert len(app.metric) >= 12
    assert any("Synthetic Data — Analytical Simulation, Not Real Company Results" in x.value
               for x in app.markdown)


def test_empty_selection_preserves_lab(app):
    app.run()
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert sum("No users match" in element.value for element in app.info) == 4
    assert any(button.label == "Run simulation" for button in app.button)


def test_lab_recalculates_and_saves_run(app):
    app.run()
    app.select_slider[0].set_value(1000)
    next(button for button in app.button if button.label == "Run simulation").click().run()
    assert not app.exception
    assert "lab_run" in app.session_state
    run = app.session_state["lab_run"]
    assert run["config"]["n_users"] == 1000
    assert set(run["summary"].variant) == {"control", "treatment"}
    next(button for button in app.button if button.label == "Save current run for comparison").click().run()
    assert not app.exception
    assert "saved_run" in app.session_state
