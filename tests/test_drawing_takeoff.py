from core.drawings.dwg_takeoff import DWGDocument, DWGEntity, infer_takeoff_from_layers
from core.drawings.bim_quantities import classify_objects, extract_quantities, link_2d_3d
from core.drawings.pdf_takeoff import PDFPageInfo, PDFTakeoffAdapter


def test_dwg_layer_quantity():
    doc = DWGDocument([
        DWGEntity("LINE", "WALL", "1", {"length": 4}),
        DWGEntity("LINE", "WALL", "2", {"length": 6}),
    ], ["WALL"])
    rows = infer_takeoff_from_layers(
        doc, {"WALL": {"description": "wall", "unit": "m", "metric": "length", "price_code": "W1"}}
    )
    assert rows[0]["quantity"] == 10
    assert rows[0]["count"] == 2
    assert rows[0]["needs_confirmation"] is False


def test_dwg_missing_metric_uses_count():
    doc = DWGDocument([
        DWGEntity("INSERT", "DOOR", "1", {"block": "D1"}),
        DWGEntity("INSERT", "DOOR", "2", {"block": "D1"}),
        DWGEntity("INSERT", "DOOR", "3", {"block": "D2"}),
    ], ["DOOR"])
    rows = infer_takeoff_from_layers(doc, {"DOOR": {"description": "doors", "unit": "count"}})
    assert rows[0]["quantity"] == 3
    assert rows[0]["count"] == 3


def test_pdf_scale_measurement():
    p = PDFTakeoffAdapter()
    assert p.normalize_scale("1:100") == 100
    assert p.normalize_scale("1 / 50") == 50
    assert p.pixel_to_model(2, "1:100", "cm") == 2
    assert round(p.measure_area(0.01, "1:100").value, 2) == 100


def test_pdf_line_measurement():
    p = PDFTakeoffAdapter()
    m = p.measure_line(0, 0, 1, 0, "1:100", "cm")
    assert m.kind == "length"
    assert m.unit == "m"
    assert m.value == 1


def test_pdf_text_candidates_and_confirmation():
    p = PDFTakeoffAdapter()
    pages = [PDFPageInfo(1, 100, 100, "Wall 250 cm\nSlab 3 m")]
    rows = p.text_takeoff_candidates(pages)
    assert len(rows) == 2
    assert rows[0]["needs_confirmation"] is True
    assert rows[0]["unit"] == "m"


def test_bim_link_and_quantities():
    class O:
        ifc_type = "IfcWall"
        global_id = "G1"
        name = "Wall"
        properties = {"Length": 5, "Area": 12, "Bad": "x"}

    rows = extract_quantities([O()])
    assert rows[0]["quantities"]["Length"] == 5
    assert rows[0]["quantities"]["Area"] == 12
    assert "Bad" not in rows[0]["quantities"]
    assert classify_objects([O()])["IfcWall"] == 1
    linked = link_2d_3d([{"global_id": "G1"}, {"global_id": "G2"}], rows)
    assert linked[0]["linked"] is True
    assert linked[1]["linked"] is False
