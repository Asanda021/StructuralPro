import pytest
from core.takeoff.boq import build_boq, boq_summary
from core.takeoff.estimate import build_estimate
from core.reports import build_report

def test_phase10_takeoff_to_boq_estimate_and_report(tmp_path):
    source_rows = [
        {"source_id": "drawing:A:01", "source_type": "takeoff", "item_code": "CONC-001",
         "price_code": "M-001", "chapter": "بتن", "category": "سازه", "group": "بتن",
         "description": "بتن فونداسیون", "quantity": 10, "unit": "m3", "unit_price": 250},
        {"source_id": "manual:02", "source_type": "takeoff", "item_code": "REBAR-001",
         "price_code": "M-002", "chapter": "آرماتور", "category": "سازه", "group": "آرماتور",
         "description": "میلگرد", "quantity": 100, "unit": "kg", "unit_price": 4},
    ]
    boq = build_boq(source_rows, aggregate=False)
    assert boq_summary(boq)["grand_total"] == pytest.approx(2900)
    assert all(row["source_id"] for row in boq)
    estimate = build_estimate(boq, aggregate=False)
    assert estimate["cost"]["base"] == pytest.approx(2900)
    report = build_report("پروژه آزمون", boq, {"grand_total": 2900})
    assert report.validate()["valid"] is True
    exported = report.export(tmp_path / "phase10.csv", "csv")
    assert exported.read_bytes().startswith(bytes.fromhex("efbbbf"))
