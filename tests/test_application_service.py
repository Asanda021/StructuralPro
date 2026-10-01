from core.platform.application import StructuralProApp

def test_application_service_offline_project_takeoff_report(tmp_path):
    a=StructuralProApp(tmp_path)
    p=a.create_project("پروژه تست","p1")
    assert p["metadata"]["offline"] is True
    row=a.add_takeoff("p1","building","slab",length=2,width=3,member_code="S1")
    assert row["quantities"][0]["amount"]==6
    assert a.open_project("p1")["takeoffs"]
    assert a.report("p1","csv",tmp_path/"r.csv").exists()


def test_counterparty_master_lifecycle_and_stable_ids(tmp_path):
    a = StructuralProApp(tmp_path)
    a.create_project("پروژه طرف حساب", "cp1")
    first = a.add_project_counterparty("cp1", "  پیمانکار   الف  ", role=" پیمانکار ")
    assert first["id"] == "CP0001"
    assert first["active"] is True
    assert a.find_project_counterparty_by_id("cp1", "CP0001")["name"] == "پیمانکار الف"

    updated = a.update_project_counterparty("cp1", "CP0001", name="پیمانکار الف جدید", role="مجری", notes="اصلی")
    assert updated["name"] == "پیمانکار الف جدید"
    assert updated["role"] == "مجری"
    assert updated["notes"] == "اصلی"

    a.set_project_counterparty_active("cp1", "CP0001", False)
    assert a.project_counterparties("cp1", active_only=True) == []
    second = a.add_project_counterparty("cp1", "فروشنده ب")
    assert second["id"] == "CP0002"
    assert a.project_counterparties("cp1")[0]["active"] is False
    try:
        a.add_project_counterparty("cp1", "پیمانکار الف جدید")
        assert False, "duplicate counterparty should be rejected"
    except ValueError:
        pass
