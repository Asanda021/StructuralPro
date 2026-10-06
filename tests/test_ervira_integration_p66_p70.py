import json
from pathlib import Path
ROOT=Path(__file__).parents[1]; C=ROOT/"contracts"/"ervira"
def load(n): return json.loads((C/f"p{n:02d}.json").read_text(encoding="utf-8"))
def test_p66_p69_closed_governance():
    for n in range(66,70):
        x=load(n); assert x["runtime_status"]=="not_implemented"; assert x["release_ready"] is False
def test_p66_audit_and_secrets_boundary():
    r=load(66)["rules"]; assert any("audit" in x for x in r); assert any("secrets" in x for x in r)
def test_p67_customer_isolation_and_provider_boundary():
    r=load(67)["rules"]; assert any("only records belonging" in x for x in r); assert any("payment provider" in x for x in r)
def test_p68_plan_change_is_attributable_and_fail_closed():
    r=load(68)["rules"]; assert any("attributable" in x for x in r); assert any("fail closed" in x for x in r)
def test_p69_failed_payment_is_auditable_and_verified():
    r=load(69)["rules"]; assert any("auditable" in x for x in r); assert any("verified billing state" in x for x in r)
def test_p70_closed_until_runtime_evidence():
    x=load(70); assert x["status"]=="closed_until_runtime_evidence"; assert x["live_customer_operations_allowed"] is False; assert x["release_ready"] is False
