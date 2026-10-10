"""Regression guards for finalizable estimates and five-storey quantity revisions.

All prices here are isolated test inputs, not an official pricebook.
"""
import pytest

from core.takeoff.estimate import build_estimate, compare_estimates
from core.takeoff.estimating import build_professional_estimate, map_prices
from core.pricing.catalog import PriceCatalog, PriceItem


def _row(source_id, quantity, price=None, code="C-01"):
    return {
        "source_id": source_id, "source": source_id, "source_type": "manual",
        "item_code": code, "price_code": code, "description": "بتن ستون",
        "unit": "m3", "quantity": quantity, "unit_price": price,
    }


def test_professional_estimate_without_catalog_cannot_finalize_unpriced_active_row():
    result = build_professional_estimate([_row("floor-1", 3)])
    assert result["finalizable"] is False
    assert result["unpriced_item_numbers"] == [1]
    assert result["cost"]["base"] == 0  # preliminary only, not an accepted price


def test_professional_estimate_accepts_explicit_zero_when_not_catalog_mapped():
    result = build_professional_estimate([_row("floor-1", 3, price=0)])
    assert result["finalizable"] is True
    assert result["unpriced_item_numbers"] == []


def test_failed_catalog_match_does_not_retain_stale_price():
    catalog = PriceCatalog([PriceItem(1404, "ابنیه", "01", "C-01", "بتن", "m3", 50)])
    stale = _row("floor-1", 3, price=999)
    stale["unit"] = "kg"
    stale["price_source"] = {"year": 1403}
    result = map_prices([stale], catalog, year=1404)
    assert result["unresolved"][0]["status"] == "unit_mismatch"
    assert result["rows"][0]["unit_price"] is None
    assert "price_source" not in result["rows"][0]
    estimate = build_professional_estimate([stale], catalog=catalog, year=1404)
    assert estimate["finalizable"] is False
    assert estimate["unpriced_item_numbers"] == [1]


def test_compare_five_storeys_preserves_all_same_code_sources():
    old = build_estimate([_row(f"floor-{i}", i, price=50) for i in range(1, 6)],
                         aggregate=False)
    new = build_estimate([_row(f"floor-{i}", i + (1 if i == 3 else 0), price=50)
                          for i in range(1, 6)], aggregate=False)
    diff = compare_estimates(old, new)
    assert diff["delta"] == 50
    assert len(diff["line_changes"]) == 1
    assert diff["line_changes"][0]["key"] == "C-01|source:floor-3"
    assert diff["line_changes"][0]["quantity_delta"] == 1
    assert diff["added_lines"] == diff["removed_lines"] == []


def test_compare_rejects_ambiguous_same_code_without_source_identity():
    rows = [_row("", 1, price=10), _row("", 2, price=10)]
    old = build_estimate(rows, aggregate=False)
    with pytest.raises(ValueError, match="ambiguous BOQ comparison identity"):
        compare_estimates(old, old)


def test_comparison_distinguishes_missing_price_from_explicit_zero():
    old = build_estimate([_row("floor-1", 1)], aggregate=False)
    new = build_estimate([_row("floor-1", 1, price=0)], aggregate=False)
    diff = compare_estimates(old, new)
    assert len(diff["line_changes"]) == 1
    change = diff["line_changes"][0]
    assert change["old_unit_price"] is None
    assert change["new_unit_price"] == 0
    assert change["unit_price_delta"] is None


def test_comparison_rejects_nonfinite_quantity_and_prices():
    old = {"cost": {"grand_total": 10}, "boq": [_row("floor-1", 1, price=10)]}
    new = {"cost": {"grand_total": 10}, "boq": [_row("floor-1", 1, price=float("inf"))]}
    with pytest.raises(ValueError, match="finite"):
        compare_estimates(old, new)


@pytest.mark.parametrize("builder", [build_estimate, build_professional_estimate])
def test_pending_human_review_blocks_finalization_even_with_explicit_price(builder):
    candidate = _row("drawing-A101-item1", 3, price=50)
    candidate["status"] = "needs_review"
    result = builder([candidate], aggregate=False)
    assert result["finalizable"] is False
    assert result["pending_item_numbers"] == [1]
    assert result["unpriced_item_numbers"] == []


@pytest.mark.parametrize("builder", [build_estimate, build_professional_estimate])
def test_cancelled_unpriced_row_does_not_block_priced_active_row(builder):
    cancelled = _row("old", 5, code="C-OLD")
    cancelled["status"] = "cancelled"
    active = _row("new", 2, price=50)
    result = builder([cancelled, active], aggregate=False)
    assert result["finalizable"] is True
    assert result["pending_item_numbers"] == []
    assert result["unpriced_item_numbers"] == []


@pytest.mark.parametrize("field", ["quantity", "unit_price", "factor", "waste_percent", "allowance_quantity"])
def test_engineering_boolean_inputs_are_rejected_in_boq(field):
    row = _row("floor-1", 3, price=10)
    row[field] = True
    with pytest.raises(ValueError, match="boolean"):
        build_estimate([row], aggregate=False)


@pytest.mark.parametrize("builder", [build_estimate, build_professional_estimate])
def test_boolean_financial_factors_are_rejected(builder):
    with pytest.raises(ValueError, match="boolean"):
        builder([_row("floor-1", 3, price=10)], factors={"ضریب": True})


def test_direct_costing_rejects_false_boolean_as_price_or_quantity():
    from core.takeoff.costing import cost_breakdown
    with pytest.raises(ValueError, match="boolean"):
        cost_breakdown([{"quantity": False, "unit_price": 10}])
    with pytest.raises(ValueError, match="boolean"):
        cost_breakdown([{"quantity": 1, "unit_price": False}])


def test_verified_catalog_zero_price_preserves_provenance_but_needs_review():
    catalog = PriceCatalog([PriceItem(1404, "ابنیه", "01", "C-01", "بتن", "m3", 0)])
    row = _row("floor-1", 1, price=999)
    mapping = map_prices([row], catalog, year=1404)
    mapped = mapping["rows"][0]
    assert mapped["price_status"] == "zero_price"
    assert mapped["unit_price"] == 0
    assert mapped["price_source"]["year"] == 1404
    assert mapping["unresolved"][0]["status"] == "zero_price"
    estimate = build_professional_estimate([row], catalog=catalog, year=1404)
    assert estimate["finalizable"] is False
    assert estimate["boq"][0]["unit_price"] == 0
