import pytest
from core.takeoff.generic import measure
from core.project.domains import normalize_discipline

def test_phase9_multidiscipline_quantities():
    cases = (
        ("معماری", "area", {"length": 10, "width": 2}, 20, "m2"),
        ("سازه", "volume", {"length": 2, "width": 3, "height": 4}, 24, "m3"),
        ("مکانیک", "length", {"length": 12}, 12, "m"),
        ("برق", "count", {"count": 8}, 8, "عدد"),
    )
    for discipline, kind, inputs, expected, unit in cases:
        result = measure(normalize_discipline(discipline), kind, **inputs)
        assert result.quantity == pytest.approx(expected)
        assert result.unit == unit

def test_phase9_invalid_quantity_fails_closed():
    with pytest.raises(ValueError):
        measure("architecture", "area", length=-1, width=2)
