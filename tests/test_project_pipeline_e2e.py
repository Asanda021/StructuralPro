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


def test_financial_dashboard_includes_actual_cost_and_gross_margin(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("داشبورد مالی", "FD1")
    app.add_takeoff(
        "FD1", "building", "wall",
        length=10, width=0.2, height=3,
        price_code="W001", unit_price=1200,
    )
    p = app.open_project("FD1")
    p["boq"][0]["current_quantity"] = 5
    app.store.save("FD1", p)
    app.add_project_cost("FD1", "مصالح", 1500)
    dash = app.financial_dashboard("FD1")
    assert dash["actual_cost"] == 1500
    assert dash["cost_entry_count"] == 1
    assert dash["gross_margin"] == dash["cumulative_work"] - 1500
    assert dash["cost_by_category"]["مصالح"] == 1500


def test_project_receipts_and_financial_position(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("دریافتی", "R1")
    app.add_takeoff("R1", "building", "wall", length=10, width=0.2, height=3, price_code="W001", unit_price=1200)
    app.add_project_cost("R1", "مصالح", 1000)
    app.add_project_receipt("R1", 5000, description="پرداخت کارفرما", reference="REC-1")
    app.add_project_receipt("R1", 2000, description="علی‌الحساب")
    receipts = app.project_receipt_summary("R1")
    assert receipts["entry_count"] == 2
    assert receipts["total_received"] == 7000
    position = app.project_financial_position("R1")
    assert position["received"] == 7000
    assert position["receivable"] == max(position["contract_amount"] - 7000, 0)
    assert position["actual_cost"] == 1000


def test_project_commitment_ledger_and_cash_exposure(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("تعهدات", "C1")
    app.add_project_commitment("C1", 12000, category="پیمانکار", description="قرارداد اجرا", paid_amount=3000)
    app.add_project_commitment("C1", 5000, category="مصالح")
    summary = app.project_commitment_summary("C1")
    assert summary["entry_count"] == 2
    assert summary["committed_total"] == 17000
    assert summary["paid_total"] == 3000
    assert summary["unpaid_total"] == 14000
    app.add_project_receipt("C1", 4000)
    pos = app.project_financial_position("C1")
    assert pos["committed_cost"] == 17000
    assert pos["unpaid_commitments"] == 14000
    assert pos["cash_exposure"] == 13000

def test_project_commitment_rejects_invalid_paid_amount(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("تعهد نامعتبر", "C2")
    with pytest.raises(ValueError):
        app.add_project_commitment("C2", 1000, paid_amount=1200)


def test_project_financial_document_center_links_ledgers_and_summarizes(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("اسناد مالی", "FDOC1")
    commitment = app.add_project_commitment("FDOC1", 12000, category="پیمانکار", paid_amount=2000)
    cost = app.add_project_cost("FDOC1", "پیمانکار", 9000, description="صورت‌حساب پیمانکار")
    receipt = app.add_project_receipt("FDOC1", 5000, description="دریافت کارفرما")
    doc = app.add_project_financial_document(
        "FDOC1", "INV-1405-001", "فاکتور پیمانکار", 9000,
        counterparty="شرکت اجرا", date="1405/07/10", due_date="1405/07/30",
        reference="REF-001", notes="فاکتور مرحله اول", payment_status="partial",
        commitment_id=commitment["id"], cost_entry_id=cost["id"], receipt_id=receipt["id"],
    )
    assert doc["id"] == 1
    assert doc["document_number"] == "INV-1405-001"
    assert doc["commitment_id"] == commitment["id"]
    assert doc["cost_entry_id"] == cost["id"]
    assert doc["receipt_id"] == receipt["id"]
    summary = app.project_financial_document_summary("FDOC1")
    assert summary["document_count"] == 1
    assert summary["document_total"] == 9000
    assert summary["by_payment_status"]["partial"] == 9000
    assert summary["by_type"]["فاکتور پیمانکار"] == 9000
    assert app.project_financial_documents("FDOC1")[0]["counterparty"] == "شرکت اجرا"


def test_project_financial_document_validates_links_and_unique_number(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("اعتبارسنجی سند", "FDOC2")
    with pytest.raises(KeyError):
        app.add_project_financial_document("FDOC2", "INV-1", "فاکتور", 1000, commitment_id=99)
    app.add_project_financial_document("FDOC2", "INV-1", "فاکتور", 1000)
    with pytest.raises(ValueError):
        app.add_project_financial_document("FDOC2", "INV-1", "فاکتور", 500)
    with pytest.raises(ValueError):
        app.add_project_financial_document("FDOC2", "INV-2", "فاکتور", 500, payment_status="unknown")


def test_project_ledger_entries_can_reference_financial_documents(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("ارتباط دفترها", "FDOC3")
    doc = app.add_project_financial_document("FDOC3", "DOC-1", "سند هزینه", 1500)
    cost = app.add_project_cost("FDOC3", "مصالح", 1500, document_id=doc["id"])
    commitment = app.add_project_commitment("FDOC3", 2000, document_id=doc["id"])
    receipt = app.add_project_receipt("FDOC3", 500, document_id=doc["id"])
    assert cost["document_id"] == doc["id"]
    assert commitment["document_id"] == doc["id"]
    assert receipt["document_id"] == doc["id"]


def test_project_financial_report_exports_consolidated_rows(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("گزارش مالی تجمیعی", "FR1")
    commitment = app.add_project_commitment("FR1", 12000, category="پیمانکار", paid_amount=3000, date="1405/07/01", due_date="1405/07/30")
    cost = app.add_project_cost("FR1", "مصالح", 2500, description="بتن", date="1405/07/02")
    receipt = app.add_project_receipt("FR1", 5000, description="پرداخت کارفرما", reference="REC-01")
    app.add_project_financial_document(
        "FR1", "INV-01", "فاکتور", 2500,
        counterparty="پیمانکار", payment_status="partial",
        commitment_id=commitment["id"], cost_entry_id=cost["id"], receipt_id=receipt["id"],
    )
    path = tmp_path / "financial.xlsx"
    result = app.project_financial_report("FR1", "xlsx", path)
    assert result == path
    assert path.exists() and path.stat().st_size > 0
    from openpyxl import load_workbook
    ws = load_workbook(path, data_only=True).active
    values = [cell.value for row in ws.iter_rows() for cell in row]
    assert "نوع" in values
    assert "سند مالی" in values
    assert "تعهد" in values
    assert "هزینه" in values
    assert "دریافتی" in values
    assert 2500 in values
    assert 12000 in values
    assert 5000 in values
