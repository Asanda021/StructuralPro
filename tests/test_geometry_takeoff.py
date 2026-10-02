from core.drawings.dwg_takeoff import DWGDocument, DWGEntity
from core.drawings.geometry_takeoff import (
    aggregate_geometry_candidates,
    extract_geometry_candidates,
)


def test_geometry_takeoff_preserves_entity_provenance_and_measures():
    entities = [
        DWGEntity("LINE", "WALL", "A1", {"length": 4}),
        DWGEntity("LINE", "WALL", "A2", {"length": 6}),
        DWGEntity("CIRCLE", "OPENING", "C1", {"area": 3.14, "length": 6.28}),
    ]
    rows = extract_geometry_candidates(entities)
    assert [r["source"] for r in rows] == ["cad:WALL:A1", "cad:WALL:A2", "cad:OPENING:C1"]
    assert rows[0]["quantity"] == 4
    assert rows[0]["unit"] == "m"
    assert rows[2]["quantity"] == 3.14
    assert rows[2]["unit"] == "m2"
    assert all(r["needs_confirmation"] for r in rows)


def test_geometry_takeoff_deduplicates_same_handle_and_aggregates_with_provenance():
    entities = [
        DWGEntity("LINE", "WALL", "A1", {"length": 4}),
        DWGEntity("LINE", "WALL", "A1", {"length": 4}),
        DWGEntity("LINE", "WALL", "A2", {"length": 6}),
    ]
    rows = aggregate_geometry_candidates(entities)
    assert len(rows) == 1
    assert rows[0]["quantity"] == 10
    assert rows[0]["entity_count"] == 2
    assert rows[0]["source"] == "cad-geometry:WALL:length"
    assert rows[0]["source_entities"] == ["cad:WALL:A1", "cad:WALL:A2"]


def test_geometry_takeoff_falls_back_to_count_for_unmeasured_entities():
    entities = [
        DWGEntity("INSERT", "DOOR", "D1", {"block": "D-01"}),
        DWGEntity("INSERT", "DOOR", "D2", {"block": "D-01"}),
    ]
    rows = extract_geometry_candidates(entities)
    assert [r["quantity"] for r in rows] == [1.0, 1.0]
    assert all(r["metric"] == "count" and r["unit"] == "عدد" for r in rows)


def test_geometry_takeoff_rejects_invalid_quantities_and_confidence():
    import math

    bad = [DWGEntity("LINE", "WALL", "A1", {"length": math.nan})]
    try:
        extract_geometry_candidates(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("non-finite CAD geometry must be rejected")

    try:
        extract_geometry_candidates([], confidence=1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid confidence must be rejected")


def test_geometry_takeoff_never_silently_uses_unknown_measurement():
    entity = DWGEntity("3DSOLID", "MODEL", "S1", {"volume": 8})
    rows = extract_geometry_candidates([entity], include_count=False)
    assert rows == []
