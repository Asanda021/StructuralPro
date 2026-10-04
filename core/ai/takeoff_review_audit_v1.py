"""P27 audit trail for AI takeoff review decisions.

Immutable-style, deterministic audit records bind a review decision to
the production package and preserve a canonical event fingerprint.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from .takeoff_production_v1 import ProductionTakeoffPackage, validate_production_package
from .takeoff_review_v1 import TakeoffReviewDecision, validate_review_decision

@dataclass(frozen=True)
class ReviewAuditRecord:
    package_fingerprint: str
    decision_fingerprint: str
    reviewer_id: str
    decision: str
    reason: str
    event: str
    audit_fingerprint: str

def _canonical(v: object) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _fp(data: dict) -> str:
    return sha256(_canonical({"schema":"p27-review-audit-v1",**data}).encode()).hexdigest()

def build_review_audit(package: ProductionTakeoffPackage, decision: TakeoffReviewDecision) -> ReviewAuditRecord:
    ok, errors = validate_review_decision(package, decision)
    if not ok:
        raise ValueError("decision is not auditable: " + "; ".join(errors))
    event = "takeoff_review_approved" if decision.decision == "approved" else "takeoff_review_rejected"
    data = {"package_fingerprint":package.fingerprint,"decision_fingerprint":decision.decision_fingerprint,
            "reviewer_id":decision.reviewer_id.strip(),"decision":decision.decision,
            "reason":decision.reason.strip(),"event":event}
    return ReviewAuditRecord(**data, audit_fingerprint=_fp(data))

def validate_review_audit(package: ProductionTakeoffPackage, record: ReviewAuditRecord) -> tuple[bool, tuple[str,...]]:
    errors=[]
    ok, package_errors=validate_production_package(package)
    if not ok: errors.extend(package_errors)
    if record.package_fingerprint != package.fingerprint: errors.append("audit package fingerprint mismatch")
    if record.decision not in {"approved","rejected"}: errors.append("invalid audit decision")
    expected_event="takeoff_review_approved" if record.decision=="approved" else "takeoff_review_rejected"
    if record.event != expected_event: errors.append("invalid audit event")
    if not record.reviewer_id.strip(): errors.append("audit reviewer identity is missing")
    if not record.reason.strip(): errors.append("audit reason is missing")
    expected=_fp({"package_fingerprint":record.package_fingerprint,"decision_fingerprint":record.decision_fingerprint,
                  "reviewer_id":record.reviewer_id.strip(),"decision":record.decision,
                  "reason":record.reason.strip(),"event":record.event})
    if record.audit_fingerprint != expected: errors.append("audit fingerprint mismatch")
    return not errors, tuple(sorted(set(errors)))
