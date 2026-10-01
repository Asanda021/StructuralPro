"""Acceptance tests for commercial report generation and output formats."""
from core.platform.application import StructuralProApp


def _seed(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("پروژه خروجی", "R1")
    app.add_takeoff(
        "R1", "building", "wall",
        length=10, width=0.2, height=3,
        price_code="W001", unit_price=1200,
    )
    app.recalculate_estimate("R1")
    return app


def test_report_export_formats(tmp_path):
    app = _seed(tmp_path)
    project = app.open_project("R1")
    rows = [
        {"کد": q.get("price_code"), "شرح": q.get("title"), "مقدار": q.get("amount"),
         "واحد": q.get("unit"), "قیمت واحد": q.get("unit_price")}
        for t in project["takeoffs"] for q in t["quantities"]
    ]
    report = __import__("core.reports.project_report", fromlist=["build_report"]).build_report(
        project["name"], rows, {"grand_total": project["estimate"]["cost"]["grand_total"]}
    )
    for fmt in ("xlsx", "pdf", "docx", "csv"):
        path = tmp_path / f"report.{fmt}"
        report.export(path, fmt)
        assert path.exists() and path.stat().st_size > 0


def test_report_service_uses_project_data(tmp_path):
    app = _seed(tmp_path)
    path = tmp_path / "report.xlsx"
    result = app.report("R1", "xlsx", path)
    assert result == path
    assert path.exists() and path.stat().st_size > 0
