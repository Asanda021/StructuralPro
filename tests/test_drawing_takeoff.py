from core.drawings.dwg_takeoff import DWGDocument,DWGEntity,infer_takeoff_from_layers
from core.drawings.bim_quantities import classify_objects,extract_quantities,link_2d_3d
from core.drawings.pdf_takeoff import PDFTakeoffAdapter

def test_dwg_layer_quantity():
    doc=DWGDocument([DWGEntity("LINE","WALL","1",{"length":4}),DWGEntity("LINE","WALL","2",{"length":6})],["WALL"])
    rows=infer_takeoff_from_layers(doc,{"WALL":{"description":"wall","unit":"m","metric":"length","price_code":"W1"}})
    assert rows[0]["quantity"]==10

def test_pdf_scale_measurement():
    p=PDFTakeoffAdapter()
    assert p.normalize_scale("1:100")==100
    assert p.pixel_to_model(2,"1:100","cm")==2
    assert round(p.measure_area(0.01,"1:100"),2)==100

def test_bim_link_and_quantities():
    class O:
        ifc_type="IfcWall"; global_id="G1"; name="Wall"
        properties={"Length":5,"Area":12}
    rows=extract_quantities([O()])
    assert rows[0]["quantities"]["Length"]==5
    assert classify_objects([O()])["IfcWall"]==1
    assert link_2d_3d([{"global_id":"G1"}],rows)[0]["linked"]
