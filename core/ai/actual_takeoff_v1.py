"""Phase 6 — production boundary for actual AI-assisted drawing takeoff.

This module connects evidence-based proposals to deterministic grouping and the
production review gate. It never derives absent quantities, never auto-accepts,
and fails closed when source identity or the proposal set is not auditable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import re
from typing import Any, Iterable, Mapping

from core.ai.takeoff_ai_v1 import AITakeoffCandidate, propose_takeoff
from core.ai.takeoff_intelligence_v1 import group_candidates
from core.ai.takeoff_production_v1 import build_production_takeoff


_INDEX_SOURCE = re.compile(r"^entity-\d+$")


@dataclass(frozen=True)
class ActualAITakeoffManifest:
    schema: str
    source_fingerprint: str
    status: str
    fail_closed: bool
    approved: bool
    candidate_count: int
    review_required_count: int
    candidates: tuple[dict[str, Any], ...]
    groups: tuple[dict[str, Any], ...]
    issues: tuple[str, ...]
    fingerprint: str


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _explicit_source(entity: Any) -> str:
    data = getattr(entity, "data", None)
    data = data if isinstance(data, Mapping) else {}
    for value in (
        data.get("source_id"),
        getattr(entity, "source_id", None),
        getattr(entity, "handle", None),
        data.get("global_id"),
        data.get("id"),
    ):
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _manifest_fingerprint(
    source_fingerprint: str,
    status: str,
    candidates: tuple[dict[str, Any], ...],
    groups: tuple[dict[str, Any], ...],
    issues: tuple[str, ...],
) -> str:
    payload = {
        "schema": "structuralpro-actual-ai-takeoff-v1",
        "source_fingerprint": source_fingerprint,
        "status": status,
        "approved": False,
        "candidates": candidates,
        "groups": groups,
        "issues": issues,
    }
    return sha256(_canonical(payload).encode("utf-8")).hexdigest()


def build_actual_ai_takeoff(
    entities: Iterable[Any],
    *,
    source_fingerprint: str,
    minimum_confidence: float = 0.70,
) -> ActualAITakeoffManifest:
    """Build a deterministic, traceable, review-only takeoff package.

    The source fingerprint must identify the actual drawing/document revision.
    Quantities must already be explicit values on parsed entities; this function
    does not infer missing dimensions, scale, geometry, or units.
    """
    fingerprint = str(source_fingerprint or "").strip()
    if not fingerprint:
        raise ValueError("source_fingerprint is required")
    if not math.isfinite(float(minimum_confidence)) or not 0 <= float(minimum_confidence) <= 1:
        raise ValueError("minimum_confidence must be finite and between 0 and 1")

    materialized = tuple(entities)
    proposals = propose_takeoff(materialized)
    issues: list[str] = []
    explicit_sources = [_explicit_source(entity) for entity in materialized]
    if any(not source for source in explicit_sources):
        issues.append("one or more drawing entities have no stable source identity")
    if not proposals:
        issues.append("no unambiguous quantity candidates were evidenced")

    proposal_sources = [source for candidate in proposals for source in candidate.source_ids]
    if len(proposal_sources) != len(set(proposal_sources)):
        issues.append("duplicate source identity across AI candidates")

    # A proposal's fallback entity-N identity is positional and therefore not
    # safe as production provenance. Reject it even if other entities are valid.
    if any(_INDEX_SOURCE.fullmatch(source) for source in proposal_sources):
        issues.append("positional source identity is not production-safe")

    groups = tuple(asdict(group) for group in group_candidates(proposals))
    production = build_production_takeoff(
        group_candidates(proposals),
        minimum_confidence=float(minimum_confidence),
    )
    issues.extend(production.issues)
    issues = tuple(sorted(set(issues)))
    blocked = bool(issues) or production.fail_closed
    status = "blocked" if blocked else "review_required"
    candidates = tuple(asdict(candidate) for candidate in proposals)
    manifest_hash = _manifest_fingerprint(fingerprint, status, candidates, groups, issues)

    return ActualAITakeoffManifest(
        schema="structuralpro-actual-ai-takeoff-v1",
        source_fingerprint=fingerprint,
        status=status,
        fail_closed=blocked,
        approved=False,
        candidate_count=len(candidates),
        review_required_count=len(candidates),
        candidates=candidates,
        groups=groups,
        issues=issues,
        fingerprint=manifest_hash,
    )


def validate_actual_ai_takeoff(manifest: ActualAITakeoffManifest) -> tuple[bool, tuple[str, ...]]:
    """Validate manifest integrity immediately before presenting human review."""
    errors = list(manifest.issues)
    if manifest.schema != "structuralpro-actual-ai-takeoff-v1":
        errors.append("unsupported manifest schema")
    if not manifest.source_fingerprint.strip():
        errors.append("missing source fingerprint")
    if manifest.approved:
        errors.append("automatic approval is forbidden")
    if manifest.candidate_count != len(manifest.candidates):
        errors.append("candidate count mismatch")
    if manifest.review_required_count != manifest.candidate_count:
        errors.append("review-required count mismatch")
    for row in manifest.candidates:
        if not row.get("source_ids"):
            errors.append("candidate without source evidence")
        try:
            quantity = float(row["quantity"])
            confidence = float(row["confidence"])
        except (KeyError, TypeError, ValueError):
            errors.append("candidate quantity/confidence missing")
            continue
        if not math.isfinite(quantity) or quantity < 0:
            errors.append("candidate quantity invalid")
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            errors.append("candidate confidence invalid")
        if row.get("needs_confirmation") is not True:
            errors.append("human confirmation gate removed")
    expected = _manifest_fingerprint(
        manifest.source_fingerprint,
        manifest.status,
        manifest.candidates,
        manifest.groups,
        manifest.issues,
    )
    if expected != manifest.fingerprint:
        errors.append("manifest fingerprint mismatch")
    if manifest.fail_closed != (manifest.status == "blocked"):
        errors.append("fail-closed status mismatch")
    if manifest.status not in {"blocked", "review_required"}:
        errors.append("invalid manifest status")
    return not errors, tuple(sorted(set(errors)))
