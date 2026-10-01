""""End-to-end acceptance for the desktop project's commercial pipeline."""
import pytest
from core.platform.application import StructuralProApp
from core.takeoff.estimate import build_estimate


# CI trigger: keep this acceptance test in the main verification path.
def test_project_pipeline_persists_estimate_and_snapshot(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("پروژه آزمایشی", "P1")
    app.add_takeoff(
        "P1", "building", "wall",
        length=10, width=0.2, height=3,
        price_code="W001", unit_price=1200,
    )
    app.add_takeoff(
        "P1", "building", "wall",
        length=5, width=0.2, height=3,
        price_code="W001", unit_price=1200,
    )

    project_before_estimate = app.open_project("P1")
    estimate = build_estimate(project_before_estimate["boq"], factors={"سربار": 0.10}, aggregate=False)
    assert estimate["summary"]["line_count"] == 1
    assert estimate["cost"]["base"] > 0
    assert estimate["cost"]["grand_total"] == pytest.approx(estimate["cost"]["base"] * 1.10)

    persisted_estimate = app.recalculate_estimate("P1")
    assert persisted_estimate["cost"]["grand_total"] == persisted_estimate["cost"]["base"]

    snapshot = app.build_commercial_snapshot("P1")
    assert snapshot["project_id"] == "P1"
    assert snapshot["estimate"]["summary"]["grand_total"] > 0
    assert len(snapshot["progress"]["lines"]) == 1

    saved = app.open_project("P1")
    assert saved["estimate"]["cost"]["grand_total"] == estimate["cost"]["grand_total"]
    assert saved["boq"][0]["price_code"] == "W001"
