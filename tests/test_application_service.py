from core.platform.application import StructuralProApp

def test_application_service_offline_project_takeoff_report(tmp_path):
    a=StructuralProApp(tmp_path)
    p=a.create_project("پروژه تست","p1")
    assert p["metadata"]["offline"] is True
    row=a.add_takeoff("p1","building","slab",length=2,width=3,member_code="S1")
    assert row["quantities"][0]["amount"]==6
    assert a.open_project("p1")["takeoffs"]
    assert a.report("p1","csv",tmp_path/"r.csv").exists()
