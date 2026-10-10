"""Offline five-floor regression: durable takeoff, recoverable backups and Persian reports.

Uses synthetic engineering inputs; no official pricebook or Windows installer.
"""
import csv
import sqlite3
from pathlib import Path

import pytest

from core.platform.application import StructuralProApp
from core.recovery.recovery import verify_database
from core.reports.project_report import build_report


def _project(tmp_path):
    data = tmp_path / "data"
    app = StructuralProApp(data)
    pid = "offline-five-floors"
    app.create_project("ساختمان پنج طبقه", pid)
    for floor in range(1, 6):
        app.add_assembly_takeoff(
            pid, "concrete_column",
            {"count": 4, "width": 0.4, "depth": 0.4, "height": 3},
            floor_id=f"طبقه {floor}", description="ستون بتنی",
        )
    return app, data, pid


def test_five_floor_reopening_json_backup_and_sqlite_backup_preserve_all_sources(tmp_path):
    app, data, pid = _project(tmp_path)
    before = app.open_project(pid)
    expected = {
        row["source_id"]: row["quantities"][0]["amount"]
        for row in before["takeoffs"]
    }
    assert len(expected) == 5
    assert sum(expected.values()) == pytest.approx(9.6)

    json_target = tmp_path / "backup" / "project.json"
    exported = app.export_project_backup(pid, json_target)
    assert exported["bytes"] > 0
    imported = app.import_project_backup(json_target)
    assert imported["id"] == pid
    assert {
        row["source_id"]: row["quantities"][0]["amount"]
        for row in imported["takeoffs"]
    } == expected

    db_target = tmp_path / "backup" / "projects.db"
    app.backup_project_database(db_target)
    assert verify_database(db_target)["ok"] is True
    with sqlite3.connect(db_target) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM projects WHERE id=?", (pid,)
        ).fetchone()[0] == 1

    app.store.close()
    reopened = StructuralProApp(data)
    actual = reopened.open_project(pid)
    assert {
        row["source_id"]: row["quantities"][0]["amount"]
        for row in actual["takeoffs"]
    } == expected
    assert reopened.project_reliability_status(pid)["integrity"]["ok"]
    assert reopened.project_performance_snapshot(pid)["collection_counts"]["takeoffs"] == 5
    assert len(reopened.project_collection_page(pid, "takeoffs", page=2, page_size=2)["items"]) == 2
    reopened.store.close()


def test_five_floor_persian_csv_and_excel_reports_remain_unpriced_and_rtl(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    app, _, pid = _project(tmp_path)
    project = app.open_project(pid)
    report = build_report(project["name"], project["boq"])
    csv_path = report.export(tmp_path / "reports" / "five.csv", "csv")
    with csv_path.open(encoding="utf-8-sig", newline="") as file:
        data = list(csv.reader(file))
    header_idx = next(i for i, cells in enumerate(data) if "شرح" in cells and "مقدار" in cells)
    header = data[header_idx]
    rows = [cells for cells in data[header_idx + 1:] if cells]
    assert len(rows) == 5
    q_index = header.index("مقدار")
    assert sum(float(row[q_index]) for row in rows) == pytest.approx(9.6)
    assert all(row[header.index("بهای واحد")] == "" for row in rows)
    assert all(row[header.index("مبلغ")] == "" for row in rows)

    xlsx = report.export(tmp_path / "reports" / "five.xlsx", "xlsx")
    wb = openpyxl.load_workbook(xlsx, read_only=False, data_only=True)
    sheet = wb["ریز متره"]
    assert sheet.sheet_view.rightToLeft is True
    headers = [cell.value for row in sheet.iter_rows() for cell in row
               if cell.value in {"شرح", "مقدار", "بهای واحد", "مبلغ"}]
    for label in ("شرح", "مقدار", "بهای واحد", "مبلغ"):
        assert label in headers
    wb.close()
    app.store.close()
