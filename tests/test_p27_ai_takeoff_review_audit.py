from dataclasses import replace
import pytest
from core.ai.takeoff_intelligence_v1 import IntelligenceGroup
from core.ai.takeoff_production_v1 import build_production_takeoff
from core.ai.takeoff_review_v1 import create_review_decision
from core.ai.takeoff_review_audit_v1 import build_review_audit, validate_review_audit

def package():
    return build_production_takeoff([IntelligenceGroup(element_type="beam",metric="length",unit="m",quantity=6,candidate_ids=("c1",),source_ids=("G1",),confidence=.9)])

def test_p27_approved_audit_is_valid():
    p=package(); d=create_review_decision(p,reviewer_id="eng-1",approve=True,reason="Checked.")
    r=build_review_audit(p,d); ok,e=validate_review_audit(p,r)
    assert ok and not e and r.event=="takeoff_review_approved"

def test_p27_rejected_audit_is_valid():
    p=package(); d=create_review_decision(p,reviewer_id="eng-1",approve=False,reason="Ambiguous.")
    r=build_review_audit(p,d); ok,e=validate_review_audit(p,r)
    assert ok and r.event=="takeoff_review_rejected"

def test_p27_tampered_audit_fails_closed():
    p=package(); d=create_review_decision(p,reviewer_id="eng-1",approve=True,reason="Checked.")
    r=build_review_audit(p,d); bad=replace(r,reason="Changed.")
    ok,e=validate_review_audit(p,bad)
    assert not ok and "audit fingerprint mismatch" in e

def test_p27_wrong_package_fails_closed():
    p=package(); d=create_review_decision(p,reviewer_id="eng-1",approve=True,reason="Checked.")
    r=build_review_audit(p,d); bad=replace(r,package_fingerprint="0"*64)
    ok,e=validate_review_audit(p,bad)
    assert not ok and "audit package fingerprint mismatch" in e

def test_p27_deterministic():
    p=package(); d=create_review_decision(p,reviewer_id="eng-1",approve=True,reason="Checked.")
    assert build_review_audit(p,d).audit_fingerprint==build_review_audit(p,d).audit_fingerprint
