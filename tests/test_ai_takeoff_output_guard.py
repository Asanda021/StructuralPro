import pytest

from core.takeoff.ai_output_guard import validate_ai_takeoff_proposal


def _proposal(**changes):
    result = {
        "quantity": 10.0, "unit": "m2", "source_ref": "plan.pdf#page=1",
        "method": "drawing_geometry", "scale_ref": "page=1; 100px=10m",
        "description": "سطح کف طبقه اول",
    }
    result.update(changes)
    return result


def test_ai_proposal_requires_explicit_user_confirmation():
    with pytest.raises(ValueError, match="تأیید صریح"):
        validate_ai_takeoff_proposal(_proposal())


def test_confirmed_proposal_is_still_marked_as_proposal():
    result = validate_ai_takeoff_proposal(_proposal(), user_confirmed=True)
    assert result.quantity == 10
    assert result.user_confirmed is True
    assert result.to_dict()["status"] == "user_confirmed_proposal"


@pytest.mark.parametrize("quantity", [float("nan"), float("inf"), -1])
def test_ai_guard_rejects_nonfinite_and_negative_quantities(quantity):
    with pytest.raises(ValueError):
        validate_ai_takeoff_proposal(_proposal(quantity=quantity), user_confirmed=True)


def test_ai_guard_rejects_missing_source_scale_and_unknown_unit():
    with pytest.raises(ValueError, match="ارجاع"):
        validate_ai_takeoff_proposal(_proposal(source_ref=""), user_confirmed=True)
    with pytest.raises(ValueError, match="کالیبراسیون"):
        validate_ai_takeoff_proposal(_proposal(scale_ref=""), user_confirmed=True)
    with pytest.raises(ValueError, match="واحد"):
        validate_ai_takeoff_proposal(_proposal(unit="mystery"), user_confirmed=True)


def test_ai_guard_does_not_require_drawing_scale_for_non_geometric_source_method():
    proposal = _proposal(method="manual_entry", scale_ref="")
    result = validate_ai_takeoff_proposal(proposal, user_confirmed=True)
    assert result.scale_ref is None
