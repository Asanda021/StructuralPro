import pytest
from core.takeoff.manual_workbench import ManualTakeoffDraft, ManualTakeoffRecord, ManualTakeoffWorkbench

def test_manual_column_entry_calculates_and_keeps_traceability():
    wb = ManualTakeoffWorkbench("project-1")
    row = wb.add_text("C1 ستون: تعداد=12، عرض=0.5، عمق=0.5، ارتفاع=3", floor_id="level-1", element_label="C1")
    assert isinstance(row, ManualTakeoffRecord)
    # 12 columns × 0.5 m × 0.5 m × 3 m = 9 m³.
    assert row.quantity == pytest.approx(9.0)
    assert row.params["count"] == pytest.approx(12.0)
    assert row.unit == "m3"
    assert row.project_id == "project-1" and row.floor_id == "level-1"
    assert row.element_label == "C1" and row.source.startswith("C1") and row.formula

def test_missing_dimensions_are_draft_not_guessed():
    wb = ManualTakeoffWorkbench("project-1", project_defaults={"height": 3})
    row = wb.add_text("ستون: تعداد=12، عرض=0.5، عمق=0.5", floor_id="level-1")
    assert isinstance(row, ManualTakeoffDraft) and row.missing == ("height",)
    assert wb.records == ()

def test_only_explicitly_confirmed_project_defaults_are_applied():
    wb = ManualTakeoffWorkbench("project-1", project_defaults={"height": 3})
    draft = wb.add_text("ستون: تعداد=2، عرض=0.4، عمق=0.4", floor_id="level-1")
    assert isinstance(draft, ManualTakeoffDraft)
    row = wb.add_text("ستون: تعداد=2، عرض=0.4، عمق=0.4", floor_id="level-1", confirmed_default_fields=("height",))
    assert isinstance(row, ManualTakeoffRecord) and row.quantity == pytest.approx(0.96)

def test_manual_batch_and_undo_redo():
    wb = ManualTakeoffWorkbench("project-1")
    rows = wb.add_batch("ستون: تعداد=2، عرض=0.4، عمق=0.4، ارتفاع=3; تیر: تعداد=3، طول=5، عرض=0.3، عمق=0.5", floor_id="level-1")
    assert len(rows) == 2 and len(wb.records) == 2
    wb.undo(); assert len(wb.records) == 1
    wb.redo(); assert len(wb.records) == 2

def test_manual_workbench_requires_project_and_floor():
    with pytest.raises(ValueError, match="project_id"): ManualTakeoffWorkbench("")
    wb = ManualTakeoffWorkbench("project-1")
    with pytest.raises(ValueError, match="floor_id"): wb.add_text("ستون: تعداد=1، عرض=0.4، عمق=0.4، ارتفاع=3", floor_id="")

def test_wall_can_explicitly_have_zero_openings():
    wb = ManualTakeoffWorkbench("project-1")
    row = wb.add_text("دیوار: تعداد=1، طول=4، ارتفاع=3، بازشو=0", floor_id="level-1")
    assert isinstance(row, ManualTakeoffRecord)
    assert row.quantity == pytest.approx(12.0)
    assert row.unit == "m2"
