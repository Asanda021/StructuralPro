import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = [f"p{i}" for i in range(51, 61)]

def load(i):
    return json.loads((ROOT / "contracts/ervira" / f"{i}.json").read_text(encoding="utf-8"))

def test_store_commercial_contracts_are_closed():
    for i in IDS:
        d = load(i)
        assert d["schema_version"] == "1.0"
        assert d["product_id"] == "structuralpro"
        assert d["parent_platform"] == "ERVIRA"
        assert d["source_contract"] == "contracts/product-contract.json"
        assert d["version"] == "0.1.0"
        assert d["runtime_status"] == "not_implemented"
        assert d["release_ready"] is False

def test_stripe_is_test_only_until_runtime_verification():
    assert load("p52")["edition_price_mapping"]["live_prices_created"] is False
    checkout = load("p54")["checkout"]
    assert checkout["provider"] == "STRIPE"
    assert checkout["mode"] == "test"
    assert checkout["live_checkout_enabled"] is False

def test_payment_must_be_verified_before_entitlement():
    p55 = load("p55")["payment_verification"]
    p57 = load("p57")["entitlement_handoff"]
    assert p55["webhook_signature_required"] is True
    assert p55["payment_verified_before_entitlement"] is True
    assert p57["requires_verified_payment"] is True
    assert p57["license_activation"] == "blocked_until_runtime_verification"

def test_subscription_lifecycle_is_event_driven():
    p58 = load("p58")["subscription_lifecycle"]
    assert p58["renewal_events_required"] is True
    assert p58["cancellation_events_required"] is True
    assert p58["failed_payment_events_required"] is True

def test_audit_is_idempotent_and_reconcilable():
    p59 = load("p59")["commercial_audit"]
    assert p59["payment_event_id_required"] is True
    assert p59["idempotency_required"] is True
    assert p59["reconciliation_required"] is True

def test_p60_is_closed_until_real_runtime_evidence_exists():
    p60 = load("p60")["store_purchase_e2e"]
    assert p60["runtime_implemented"] is False
    assert p60["verification_implemented"] is False
    assert p60["live_purchase_allowed"] is False
    assert p60["release_ready"] is False
