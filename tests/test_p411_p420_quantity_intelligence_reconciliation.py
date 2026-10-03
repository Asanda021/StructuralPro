from core.takeoff.quantity_reconciliation_v1 import QuantityEvidence, QuantityReconciler
import pytest

def q(i,s,n,u="m3",rev="A",status="accepted"):
    return QuantityEvidence(i,s,n,u,rev,status)

def test_matching_sources_reconcile():
    out=QuantityReconciler().reconcile([q("R1","D1",10),q("R1","B1",10)])
    assert out[0]["status"]=="matched"

def test_conflicting_quantities_require_review():
    out=QuantityReconciler().reconcile([q("R1","D1",10),q("R1","B1",12)])
    assert out[0]["status"]=="review"

def test_units_are_part_of_identity():
    out=QuantityReconciler().reconcile([q("R1","D1",10,"m3"),q("R1","B1",10,"m2")])
    assert len(out)==2

def test_unaccepted_fails_closed():
    with pytest.raises(ValueError):
        q("R1","D1",10,status="review").validate()

def test_negative_fails_closed():
    with pytest.raises(ValueError):
        q("R1","D1",-1).validate()

def test_duplicate_sources_are_explicit():
    d=QuantityReconciler().duplicates([q("R1","D1",10),q("R1","D1",10)])
    assert len(d)==1

def test_fingerprint_is_deterministic():
    a=[q("R1","D1",10),q("R2","D2",5)]
    b=list(reversed(a))
    assert QuantityReconciler.fingerprint(a)==QuantityReconciler.fingerprint(b)
