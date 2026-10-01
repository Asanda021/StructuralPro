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
    assert saved["estimate"]["cost"]["grand_total"] == snapshot["estimate"]["cost"]["grand_total"]
    assert saved["boq"][0]["price_code"] == "W001"

def test_financial_dashboard_summarizes_contract_progress_and_statements(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("پروژه مالی", "D1")
    app.add_takeoff(
        "D1", "building", "wall",
        length=10, width=0.2, height=3,
        price_code="W001", unit_price=1200,
    )
    p = app.open_project("D1")
    p["boq"][0]["current_quantity"] = 5
    app.store.save("D1", p)
    period = app.save_statement_period("D1", current_quantities={"W001": 5})
    dash = app.financial_dashboard("D1")
    assert dash["project_name"] == "پروژه مالی"
    assert dash["line_count"] == 1
    assert dash["contract_amount"] > 0
    assert dash["cumulative_work"] == period["completed_total"]
    assert dash["statement_count"] == 1
    assert dash["latest_statement_no"] == 1
    assert dash["latest_payable"] == period["payable_current"]
    assert 0 <= dash["progress_percent"] <= 100


def test_project_financial_control_calculates_cost_variance(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("کنترل مالی", "F1")
    app.add_takeoff(
        "F1", "building", "wall",
        length=10, width=0.2, height=3,
        price_code="W001", unit_price=1200,
    )
    p = app.open_project("F1")
    p["boq"][0]["current_quantity"] = 5
    app.store.save("F1", p)
    control = app.project_financial_control("F1", planned_cost=5000, actual_cost=4000)
    assert control["earned_value"] == 6000
    assert control["cost_variance"] == 2000
    assert control["schedule_variance"] == pytest.approx(6000 - (5000 * (6000 / 36000)))
    assert control["cost_performance_index"] == pytest.approx(1.5)


def test_project_cost_ledger_persists_and_feeds_financial_control(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("دفتر هزینه", "C1")
    app.add_takeoff(
        "C1", "building", "wall",
        length=10, width=0.2, height=3,
        price_code="W001", unit_price=1200,
    )
    app.open_project("C1")["boq"][0]["current_quantity"] = 5
    p = app.open_project("C1")
    p["boq"][0]["current_quantity"] = 5
    app.store.save("C1", p)
    first = app.add_project_cost("C1", "مصالح", 1500, description="خرید سیمان", date="1405/07/09")
    second = app.add_project_cost("C1", "دستمزد", 500)
    summary = app.project_cost_summary("C1")
    assert first["id"] == 1 and second["id"] == 2
    assert summary["entry_count"] == 2
    assert summary["actual_cost"] == 2000
    assert summary["by_category"]["مصالح"] == 1500
    control = app.project_financial_control("C1")
    assert control["actual_cost"] == 2000


def test_project_cost_report_exports_rows_and_category_totals(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("گزارش هزینه", "CR1")
    app.add_project_cost("CR1", "مصالح", 1200, description="بتن", date="1405/07/01")
    app.add_project_cost("CR1", "دستمزد", 800, description="اجرای سقف", date="1405/07/02")
    path = tmp_path / "costs.xlsx"
    result = app.project_cost_report("CR1", "xlsx", path)
    assert result == path
    assert path.exists() and path.stat().st_size > 0
    from openpyxl import load_workbook
    ws = load_workbook(path, data_only=True).active
    values = [cell.value for row in ws.iter_rows() for cell in row]
    assert "مبلغ نهایی" in values
    assert 2000 in values
    assert "مصالح" in values
    assert "دستمزد" in values
