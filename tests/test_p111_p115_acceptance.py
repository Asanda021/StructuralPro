import hashlib
from core.acceptance.p111_p115 import (
    ingest_official_price_csv, build_professional_report_pack,
    build_revision_acceptance, run_large_project_hardening, build_release_readiness,
)

def price_csv():
    return "code,description,unit,unit_price\nA01,Concrete,m3,1250\nA02,Rebar,kg,42\n"

def test_p111_authorized_price_import_is_checksum_and_provenance_bound():
    text = price_csv()
    digest = hashlib.sha256(text.encode()).hexdigest()
    result = ingest_official_price_csv(text, source={
        "publisher":"سازمان برنامه و بودجه کشور","edition":"1404",
        "source_url":"https://example.gov/price.csv","sha256":digest,
    })
    assert result["row_count"] == 2
    assert result["checksum_verified"] is True
    assert result["source_verified"] is False
    assert result["provenance_complete"] is True

def test_p111_tampered_dataset_fails_closed():
    text = price_csv()
    digest = hashlib.sha256(text.encode()).hexdigest()
    try:
        ingest_official_price_csv(text+"A03,X,kg,1\n", source={
            "publisher":"P","edition":"E","source_url":"https://example.gov/x","sha256":digest})
        assert False
    except ValueError as exc:
        assert "checksum" in str(exc)

def test_p112_professional_rtl_report_pack():
    result = build_professional_report_pack("P112-1", [
        {"item_no":1,"description":"بتن","quantity":10,"unit":"m3","unit_price":100,"total":1000},
        {"item_no":2,"description":"میلگرد","quantity":500,"unit":"kg","unit_price":50,"total":25000},
    ], "R3")
    assert result["ready"] and result["rtl"] and result["report"]["totals"]["amount"] == 26000

def test_p113_revision_requires_explicit_review_then_can_finalize():
    before=[{"object_id":"B1","quantity":10,"concrete_volume_m3":10,"cost":1000}]
    after=[{"object_id":"B1","quantity":12,"concrete_volume_m3":12,"cost":1200}]
    pending=build_revision_acceptance(before,after)
    assert pending["summary"]["changed"] == 1 and not pending["finalizable"]
    approved=build_revision_acceptance(before,after,{"B1":True})
    assert approved["finalizable"] and approved["changes"][0]["review_status"]=="approved"

def test_p114_large_project_gate_is_deterministic():
    result=run_large_project_hardening(5000)
    assert result["change_count"] == 100
    assert result["finite"] and result["within_gate"] and result["deterministic"]

def test_p115_release_readiness_has_external_evidence_boundary():
    result=build_release_readiness()
    assert result["version_valid"] and result["hardening"]["ok"]
    assert "authorized_iran_price_dataset" in result["external_evidence_required"]
    assert result["offline_core"] is True
