import json
from pathlib import Path

import pytest

from core.takeoff.assembly import calculate_assembly


FIXTURE = Path(__file__).parent / "fixtures" / "golden_five_storey_building_v1.json"


def test_five_storey_golden_dataset_matches_all_reference_components():
    dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert dataset["schema_version"] == 1
    assert dataset["building"]["storeys"] == 5
    assert dataset["building"]["currency"] is None
    assert dataset["building"]["pricebook"] is None

    actual_totals = {}
    for case in dataset["cases"]:
        result = calculate_assembly(case["assembly"], **case["inputs"])
        assert result.complete, f"{case['id']}: missing inputs {result.missing_inputs}"
        components = {component.code: component for component in result.components}
        assert set(case["expected_per_repeat"]).issubset(components), case["id"]
        for code, expected in case["expected_per_repeat"].items():
            component = components[code]
            assert component.unit == case["units"][code], f"{case['id']}:{code} unit"
            assert component.quantity == pytest.approx(expected, abs=1e-8), f"{case['id']}:{code}"
            total_key = {
                ("foundation-excavation", "excavation"): "excavation",
                ("columns-per-storey", "concrete"): "column_concrete",
                ("slab-per-storey", "concrete"): "slab_concrete",
                ("beams-per-storey", "concrete"): "beam_concrete",
                ("beams-per-storey", "formwork"): "beam_formwork",
                ("beams-per-storey", "reinforcement"): "beam_reinforcement",
                ("masonry-per-storey", "wall_area"): "masonry_area",
                ("masonry-per-storey", "block"): "masonry_blocks",
                ("floor-finish-per-storey", "finish_area"): "floor_finish_area",
            }.get((case["id"], code))
            if total_key:
                actual_totals[total_key] = component.quantity * case["repeat_count"]

    for key, expected in dataset["expected_building_totals"].items():
        assert actual_totals[key] == pytest.approx(expected["quantity"], abs=1e-8), key


def test_golden_dataset_does_not_inject_hidden_waste_or_prices():
    dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for case in dataset["cases"]:
        assert "waste_factor" not in case["inputs"], case["id"]
        assert "unit_price" not in case["inputs"], case["id"]
        assert "price" not in case["inputs"], case["id"]


def test_five_storey_golden_dataset_round_trips_through_persistent_project_and_boq(tmp_path):
    from core.platform.application import StructuralProApp

    dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))
    app = StructuralProApp(tmp_path)
    app.create_project(dataset["title"], dataset["dataset_id"])
    for case in dataset["cases"]:
        repeats = case["repeat_count"]
        floors = range(1, repeats + 1) if repeats > 1 else (0,)
        for floor_index in floors:
            floor = f"طبقه {floor_index}" if floor_index else "فونداسیون"
            app.add_assembly_takeoff(
                dataset["dataset_id"], case["assembly"], case["inputs"],
                floor_id=floor, description=f"{case['id']} — {floor}",
            )

    project = app.open_project(dataset["dataset_id"])
    assert len(project["takeoff_assemblies"]) == sum(case["repeat_count"] for case in dataset["cases"])
    assert project["takeoffs"]
    assert project["boq"]
    by_code = {}
    for row in project["boq"]:
        key = row.get("item_code") or row.get("price_code")
        by_code[key] = by_code.get(key, 0.0) + float(row["quantity"])

    expected = {
        "excavation": 54.0,
        "concrete": 295.5,
        "formwork": 260.0,
        "reinforcement": 3600.0,
        "wall_area": 130.0,
        "block": 1510.0,
        "mortar": 1.842044134727061,
        "cement": 0.3684088269454122,
        "sand": 1.473635307781649,
        "finish_area": 1450.0,
    }
    for code, quantity in expected.items():
        assert by_code[code] == pytest.approx(quantity, abs=1e-8), code
    assert all(row.get("unit_price") is None and row.get("total") is None for row in project["boq"])


def test_five_storey_independent_oracle_estimate_and_export(tmp_path):
    """Independent decimal arithmetic; no production prices or engineering acceptance."""
    import csv
    from decimal import Decimal as D
    from core.platform.application import StructuralProApp
    from core.reports.project_report import build_report

    dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))
    app = StructuralProApp(tmp_path / "data")
    project_id = dataset["dataset_id"]
    app.create_project(dataset["title"], project_id)
    for case in dataset["cases"]:
        for floor in range(case["repeat_count"]):
            app.add_assembly_takeoff(project_id, case["assembly"], case["inputs"],
                                    floor_id=str(floor + 1), description=case["id"])
    reopened = StructuralProApp(tmp_path / "data")
    project = reopened.open_project(project_id)
    oracle = {
        "excavation": D(20) * D('1.5') ** 2 * D('1.2'),
        "concrete": D(5) * (D(20) * D('.4') ** 2 * D(3)
                     + (D(20) * D(15) - D(10)) * D('.15')
                     + D(2) * D(20) * D('.3') * D('.5')),
        "formwork": D(5) * D(2) * D(20) * (D('.3') + D(2) * D('.5')),
        "reinforcement": D(5) * D(2) * D(20) * D('.3') * D('.5') * D(120),
        "wall_area": D(5) * (D(10) * D(3) - D(4)),
        "finish_area": D(5) * (D(20) * D(15) - D(10)),
    }
    estimate = reopened.recalculate_estimate(project_id)
    assert estimate["finalizable"] is False  # Missing prices cannot become a payable estimate.
    report = build_report(project["name"], project["boq"], metadata={"نوع داده": dataset["status"]})
    path = report.export(tmp_path / "five-storey.csv", "csv")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        lines = list(csv.reader(fh))
    header_index = next(i for i, row in enumerate(lines) if "کد آیتم" in row)
    header = lines[header_index]
    totals = {}
    for row in lines[header_index + 1:]:
        code = row[header.index("کد آیتم")]
        totals[code] = totals.get(code, D(0)) + D(row[header.index("مقدار")])
        assert row[header.index("بهای واحد")] == ""
        assert row[header.index("مبلغ")] == ""
    for code, expected in oracle.items():
        assert float(totals[code]) == pytest.approx(float(expected), abs=1e-8)
    assert reopened.project_reliability_status(project_id)["integrity"]["ok"] is True
