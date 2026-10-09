import pytest

from core.drawings.takeoff_bridge import prepare_drawing_takeoff_rows


def _item(**changes):
    row = {
        "id": "TO-00001", "kind": "area", "quantity": 12.5, "page": 2,
        "source": "page:2:area:1", "source_ref": "plan.pdf#page=2&takeoff=TO-00001",
        "formula": "125 px² × 0.1²", "label": "سطح کف",
    }
    row.update(changes)
    return row


def test_bridge_creates_reviewable_traceable_row_without_claiming_approval():
    rows = prepare_drawing_takeoff_rows([_item()], drawing_source="plan.pdf")
    assert len(rows) == 1
    assert rows[0].source_id == "drawing:plan.pdf:page:2:TO-00001"
    assert rows[0].quantity == 12.5
    assert rows[0].unit == "m2"
    assert rows[0].status == "needs_review"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 0])
def test_bridge_rejects_invalid_quantity(bad):
    with pytest.raises(ValueError):
        prepare_drawing_takeoff_rows([_item(quantity=bad)], drawing_source="plan.pdf")


def test_bridge_rejects_missing_source_or_formula():
    with pytest.raises(ValueError, match="منبع"):
        prepare_drawing_takeoff_rows([_item(source_ref="")], drawing_source="plan.pdf")
    with pytest.raises(ValueError, match="فرمول"):
        prepare_drawing_takeoff_rows([_item(formula="")], drawing_source="plan.pdf")


def test_bridge_rejects_duplicate_source_to_prevent_double_counting():
    with pytest.raises(ValueError, match="تکراری"):
        prepare_drawing_takeoff_rows([_item(), _item(id="TO-00002")], drawing_source="plan.pdf")


def test_bridge_rejects_missing_drawing_identity_and_unsupported_kind():
    with pytest.raises(ValueError, match="شناسه/مسیر"):
        prepare_drawing_takeoff_rows([_item()], drawing_source="")
    with pytest.raises(ValueError, match="پشتیبانی"):
        prepare_drawing_takeoff_rows([_item(kind="unknown")], drawing_source="plan.pdf")
