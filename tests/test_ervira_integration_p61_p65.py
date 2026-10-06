import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONTRACTS = ROOT / "contracts" / "ervira"

def load(n):
    return json.loads((CONTRACTS / f"p{n:02d}.json").read_text(encoding="utf-8"))

def test_p61_p64_governance_closed():
    for n in range(61, 65):
        c = load(n)
        assert c["runtime_status"] == "not_implemented"
        assert c["release_ready"] is False
        assert c["status"] == "governance_ready"

def test_p61_does_not_store_payment_method_data():
    c = load(61)
    assert "payment_method_data" not in c["rules"]
    assert any("no payment method data" in r for r in c["rules"])

def test_p62_requires_verified_payment_and_unique_invoice():
    rules = load(62)["rules"]
    assert any("verified payment" in r for r in rules)
    assert any("unique" in r for r in rules)

def test_p63_refunds_are_idempotent_and_do_not_silently_grant_entitlement():
    rules = load(63)["rules"]
    assert any("idempotent" in r for r in rules)
    assert any("cannot silently grant" in r for r in rules)

def test_p64_tax_is_fail_closed_and_provenance_bound():
    rules = load(64)["rules"]
    assert any("unsupported jurisdictions fail closed" in r for r in rules)
    assert any("source evidence" in r for r in rules)

def test_p65_is_closed_until_real_runtime_evidence():
    c = load(65)
    assert c["status"] == "closed_until_runtime_evidence"
    assert c["live_billing_allowed"] is False
    assert c["runtime_status"] == "not_implemented"
    assert c["release_ready"] is False
