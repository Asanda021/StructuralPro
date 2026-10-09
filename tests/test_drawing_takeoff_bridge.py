import copy
from dataclasses import replace

import pytest

from core.drawings.graphical_takeoff import Point
from core.drawings.takeoff_bridge import build_takeoff_export_payload, session_to_boq_rows
from core.drawings.takeoff_session import DrawingTakeoffSession


def _session():
    session = DrawingTakeoffSession('plan.pdf')
    session.calibrate(1, 100, 10)
    session.add_length([Point(0, 0), Point(100, 0)], page=1,
                       label='دیوار', takeoff_code='WALL-01')
    return session


def test_export_keeps_review_contract_and_preserves_persistent_bridge():
    session = _session()
    before = copy.deepcopy(session.to_dict())
    payload = build_takeoff_export_payload(session)
    row = payload['items'][0]
    persistent = session_to_boq_rows(before, session_id='saved-1',
                                     selected_item_ids=[session.items[0].id])[0]
    assert payload['schema'] == 'structuralpro.drawing-takeoff.v1'
    assert payload['approval_required'] is True
    assert payload['summary'] == {'items': 1, 'needs_review': 1, 'by_unit': {'m': 10.0}}
    assert row['status'] == 'needs_review'
    assert row['source_id'] == 'drawing:plan.pdf:page:1:TO-00001'
    assert row['source_ref'] == persistent['source'] == 'plan.pdf#page=1&takeoff=TO-00001'
    assert row['quantity'] == persistent['quantity'] == 10
    assert row['takeoff_code'] == persistent['item_code'] == 'WALL-01'
    assert session.to_dict() == before


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -1, 0])
def test_export_rejects_invalid_quantities_through_canonical_validator(bad):
    session = _session()
    session.items[0] = replace(session.items[0], quantity=bad)
    with pytest.raises(ValueError):
        build_takeoff_export_payload(session)


@pytest.mark.parametrize('field,value', [
    ('source_ref', ''), ('source_ref', 'other.pdf#page=1&takeoff=TO-00001'),
    ('formula', ''), ('kind', 'unknown'),
])
def test_export_rejects_incomplete_or_mismatched_provenance(field, value):
    session = _session()
    session.items[0] = replace(session.items[0], **{field: value})
    with pytest.raises(ValueError):
        build_takeoff_export_payload(session)


def test_export_rejects_duplicate_measurements_and_missing_page_calibration():
    session = _session()
    session.items.append(copy.deepcopy(session.items[0]))
    with pytest.raises(ValueError, match='تکراری'):
        build_takeoff_export_payload(session)
    session = _session()
    session.calibrations.clear()
    with pytest.raises(ValueError):
        build_takeoff_export_payload(session)


def test_export_rejects_missing_source_and_empty_session():
    session = _session()
    session.drawing_source = ''
    with pytest.raises(ValueError):
        build_takeoff_export_payload(session)
    with pytest.raises(ValueError):
        build_takeoff_export_payload(DrawingTakeoffSession('plan.pdf'))
