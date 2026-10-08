from core.takeoff.manual_input import parse_manual_batch, parse_manual_entry

def test_persian_column_quick_entry():
    r=parse_manual_entry("۱۲ ستون 50x50 ارتفاع 3")
    assert r.code=="column"
    assert r.params["count"]==12
    assert r.params["width"]==0.5
    assert r.params["depth"]==0.5
    assert r.params["height"]==3
    assert r.complete

def test_named_column_entry_needs_only_missing_geometry():
    r=parse_manual_entry("ستون: تعداد=12، عرض=0.5، عمق=0.5")
    assert r.code=="column"
    assert r.missing==("height",)

def test_manual_batch_accepts_multiple_operations():
    rows=parse_manual_batch("ستون: تعداد=12، عرض=0.5، عمق=0.5، ارتفاع=3; تیر: تعداد=18، طول=5.2، عرض=0.3، عمق=0.5")
    assert len(rows)==2
    assert rows[0].complete and rows[1].complete

def test_manual_input_never_invents_missing_values():
    r=parse_manual_entry("پله: تعداد=1، عرض=1.2")
    assert not r.complete
    assert "sloped_length" in r.missing
    assert "waist_thickness" in r.missing
