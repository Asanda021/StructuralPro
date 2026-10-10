"""Project-level drawing provenance and BOQ commit invariants."""
from dataclasses import replace

import pytest

from core.drawings.graphical_takeoff import Point
from core.drawings.takeoff_session import DrawingTakeoffSession
from core.platform.application import StructuralProApp


def _session(path="plan.pdf", *, area=False):
    session = DrawingTakeoffSession(path)
    session.calibrate(1, 100, 10)
    if area:
        item = session.add_area(
            [Point(0, 0), Point(100, 0), Point(100, 100), Point(0, 100)],
            holes=[[Point(10, 10), Point(20, 10), Point(20, 20), Point(10, 20)]],
            label="دیوار با بازشو", takeoff_code="W-01",
        )
    else:
        item = session.add_length(
            [Point(0, 0), Point(100, 0)], label="دیوار", takeoff_code="W-01",
        )
    return session, item


def _project(tmp_path):
    app = StructuralProApp(tmp_path)
    app.create_project("پروژه کنترل منشأ", "p1")
    return app


def test_committed_drawing_measurement_cannot_be_edited_in_saved_session(tmp_path):
    app = _project(tmp_path)
    session, item = _session()
    saved = app.save_drawing_takeoff_session("p1", session)
    committed = app.commit_drawing_takeoff_to_boq(
        "p1", saved["session_id"], [item.id], expected_session_revision=1
    )
    original = app.open_project("p1")
    session.items[0] = replace(session.items[0], label="شرح ویرایش‌شده")
    with pytest.raises(ValueError, match="نباید حذف یا ویرایش"):
        app.save_drawing_takeoff_session(
            "p1", session, session_id=saved["session_id"],
            expected_revision=committed["revision"],
        )
    after = app.open_project("p1")
    assert after["boq"] == original["boq"]
    assert after["drawing_sessions"][saved["session_id"]]["revision"] == 2


def test_removing_committed_measurement_is_blocked_but_adding_new_one_is_allowed(tmp_path):
    app = _project(tmp_path)
    session, first = _session()
    saved = app.save_drawing_takeoff_session("p1", session)
    committed = app.commit_drawing_takeoff_to_boq(
        "p1", saved["session_id"], [first.id], expected_session_revision=1
    )
    session.remove(first.id)
    with pytest.raises(ValueError, match="نباید حذف"):
        app.save_drawing_takeoff_session(
            "p1", session, session_id=saved["session_id"],
            expected_revision=committed["revision"],
        )
    # Start again from the originally committed session, not the rejected edit.
    restored = DrawingTakeoffSession.from_dict(
        app.load_drawing_takeoff_session("p1", saved["session_id"])["session"]
    )
    next_item = restored.add_count(2, label="درب")
    resaved = app.save_drawing_takeoff_session(
        "p1", restored, session_id=saved["session_id"],
        expected_revision=committed["revision"],
    )
    assert resaved["revision"] == 3
    assert resaved["committed_item_ids"] == [first.id]
    assert next_item.id != first.id


def test_same_drawing_item_cannot_be_committed_from_two_different_sessions(tmp_path):
    app = _project(tmp_path)
    first, item = _session()
    second, _ = _session()  # same source path, page, ID and geometry
    one = app.save_drawing_takeoff_session("p1", first)
    two = app.save_drawing_takeoff_session("p1", second)
    app.commit_drawing_takeoff_to_boq(
        "p1", one["session_id"], [item.id], expected_session_revision=1
    )
    with pytest.raises(ValueError, match="منبع متره قبلاً"):
        app.commit_drawing_takeoff_to_boq(
            "p1", two["session_id"], [item.id], expected_session_revision=1
        )
    assert len(app.open_project("p1")["takeoffs"]) == 1
    assert app.load_drawing_takeoff_session("p1", two["session_id"])["revision"] == 1


def test_duplicate_explicit_selection_rejected_without_mutation(tmp_path):
    app = _project(tmp_path)
    session, item = _session()
    saved = app.save_drawing_takeoff_session("p1", session)
    with pytest.raises(ValueError, match="تکراری"):
        app.commit_drawing_takeoff_to_boq(
            "p1", saved["session_id"], [item.id, item.id],
            expected_session_revision=1,
        )
    assert app.open_project("p1")["takeoffs"] == []


def test_area_openings_and_provenance_are_kept_in_persisted_takeoff(tmp_path):
    app = _project(tmp_path)
    session, item = _session(area=True)
    saved = app.save_drawing_takeoff_session("p1", session)
    app.commit_drawing_takeoff_to_boq(
        "p1", saved["session_id"], [item.id], expected_session_revision=1
    )
    reopened = StructuralProApp(tmp_path)
    row = reopened.open_project("p1")["takeoffs"][0]
    assert row["params"]["holes"] == [[[10, 10], [20, 10], [20, 20], [10, 20]]]
    assert row["params"]["source_ref"] == "plan.pdf#page=1&takeoff=TO-00001"
    assert row["quantities"][0]["amount"] == pytest.approx(99)
