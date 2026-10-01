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


def test_financial_reconciliation_audits_status_without_mutation(tmp_path):
    a = StructuralProApp(tmp_path)
    a.create_project("پروژه تطبیق", "rec1")
    cp = a.add_project_counterparty("rec1", "طرف حساب")
    commitment = a.add_project_commitment("rec1", 1000, paid_amount=400, counterparty=cp["name"])
    a.add_project_financial_document("rec1", "DOC-1", "فاکتور", 1000, counterparty=cp["name"],
                                     payment_status="unpaid", commitment_id=commitment["id"])
    a.add_project_financial_document("rec1", "DOC-2", "فاکتور", 500, counterparty=cp["name"],
                                     payment_status="paid")
    receipt = a.add_project_receipt("rec1", 500, counterparty=cp["name"])
    p = a.open_project("rec1")
    p["financial_documents"][1]["receipt_id"] = receipt["id"]
    a.store.save("rec1", p)

    result = a.project_financial_reconciliation("rec1")
    assert result["document_count"] == 2
    assert result["mismatch_count"] == 1
    assert result["unlinked_count"] == 0
    assert result["rows"][0]["derived_status"] == "partial"
    assert result["rows"][0]["status_match"] is False
    assert result["rows"][1]["derived_status"] == "paid"
    assert a.project_financial_documents("rec1")[0]["payment_status"] == "unpaid"
    assert a.project_financial_reconciliation_report("rec1", "csv", tmp_path/"reconciliation.csv").exists()
