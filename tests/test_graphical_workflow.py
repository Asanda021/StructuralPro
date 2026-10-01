from core.drawings.graphical_takeoff import ScaleCalibration,Point,MeasurementStore,polygon_area,subtract_areas,snap_point
from core.takeoff.assemblies import AssemblyLibrary
from core.takeoff.workflow import TakeoffWorkflow
from core.ai.auto_takeoff import LocalAutoTakeoff

def test_scale_and_geometry():
    s=ScaleCalibration.parse("1:100",drawing_unit="cm")
    assert round(s.length(2),2)==2
    assert round(s.area(1),2)==1
    pts=[Point(0,0),Point(2,0),Point(2,3),Point(0,3)]
    assert polygon_area(pts)==6
    assert subtract_areas(6,[1,2])==3
    assert snap_point(Point(2.01,2.99),[Point(2,3)],.05)==Point(2,3)

def test_graphical_store():
    s=ScaleCalibration.parse("1:100",drawing_unit="cm")
    m=MeasurementStore()
    a=m.add_length([Point(0,0),Point(2,0)],s,page=1,label="دیوار")
    b=m.add_area([Point(0,0),Point(2,0),Point(2,2),Point(0,2)],s,page=1,label="کف")
    c=m.add_count(4,page=1,label="در")
    assert a.unit=="m" and round(a.value,2)==2
    assert b.unit=="m2" and round(b.value,2)==4
    assert c.value==4
    assert m.summary()["count"]==3

def test_assemblies_are_reusable_and_deterministic():
    lib=AssemblyLibrary()
    x=lib.expand("SLAB-CON",10)
    assert any(i["code"]=="REBAR" and i["quantity"]==120 for i in x)
    assert sum(i["cost"] for i in x)==0

def test_local_auto_takeoff():
    class E:
        layer="WALL"
        entity_type="LINE"
        data={"length":5}
    ai=LocalAutoTakeoff()
    rows=ai.auto_takeoff([E()])
    assert rows[0]["kind"]=="wall" and rows[0]["quantity"]==5
    assert rows[0]["needs_confirmation"] is True
    assert ai.auto_scale("Plan 1:100") == 100

def test_end_to_end_workflow_is_reviewable():
    w=TakeoffWorkflow()
    rows=[{"description":"concrete wall","quantity":10,"unit":"m2","price_code":"A1"}]
    out=w.build_estimate(rows,{"A1":250})
    assert out[0]["total"]==2500
    mapped=w.map_price_codes(rows,[{"code":"A1","description":"concrete wall","group":"building","chapter":"concrete"}])
    assert mapped[0]["price_code"]=="A1"

