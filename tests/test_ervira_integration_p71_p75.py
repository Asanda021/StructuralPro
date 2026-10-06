import json
from pathlib import Path
ROOT=Path(__file__).parents[1]; C=ROOT/"contracts"/"ervira"
def load(n): return json.loads((C/f"p{n:02d}.json").read_text(encoding="utf-8"))

def test_p71_p74_closed_governance():
    for n in range(71,75):
        x=load(n)
        assert x["runtime_status"]=="not_implemented"
        assert x["release_ready"] is False

def test_p71_support_attribution_and_boundary():
    r=load(71)["rules"]
    assert any("authenticated customer context" in x for x in r)
    assert any("auditable" in x for x in r)
    assert any("secrets" in x for x in r)

def test_p72_notifications_verified_and_idempotent():
    r=load(72)["rules"]
    assert any("verified lifecycle event" in x for x in r)
    assert any("idempotent" in x for x in r)
    assert any("sensitive payment data" in x for x in r)

def test_p73_export_isolated_and_fail_closed():
    r=load(73)["rules"]
    assert any("authenticated customer's authorized records" in x for x in r)
    assert any("fail closed" in x for x in r)

def test_p74_security_audit_and_secret_boundary():
    r=load(74)["rules"]
    assert any("auditable" in x for x in r)
    assert any("authenticated customer context" in x for x in r)
    assert any("session secrets" in x for x in r)

def test_p75_closed_until_runtime_evidence():
    x=load(75)
    assert x["status"]=="closed_until_runtime_evidence"
    assert x["live_customer_trust_operations_allowed"] is False
    assert x["release_ready"] is False
