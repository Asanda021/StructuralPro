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
