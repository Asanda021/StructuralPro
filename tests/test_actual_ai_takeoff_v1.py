from dataclasses import replace

import pytest

from core.ai.actual_takeoff_v1 import (
    build_actual_ai_takeoff,
    validate_actual_ai_takeoff,
)
from core.drawings.dwg_takeoff import DWGEntity


def entity(handle="beam-01", *, layer="BEAM", data=None):
    payload = {"length": 6.0, "source_id": handle, "text": "beam"}
    payload.update(data or {})
    return DWGEntity("LINE", layer, handle, payload)


def test_actual_ai_takeoff_is_deterministic_and_review_only():
    rows = [entity()]
    first = build_actual_ai_takeoff(rows, source_fingerprint="sha256:drawing-A")
    second = build_actual_ai_takeoff(rows, source_fingerprint="sha256:drawing-A")
    assert first.status == "review_required"
    assert first.fail_closed is False
    assert first.approved is False
    assert first.candidate_count == 1
    assert first.review_required_count == 1
    assert first.fingerprint == second.fingerprint
    assert validate_actual_ai_takeoff(first) == (True, ())


def test_drawing_revision_fingerprint_changes_manifest_fingerprint():
    rows = [entity()]
    first = build_actual_ai_takeoff(rows, source_fingerprint="sha256:rev-A")
    second = build_actual_ai_takeoff(rows, source_fingerprint="sha256:rev-B")
    assert first.fingerprint != second.fingerprint


def test_missing_stable_source_identity_fails_closed():
    row = DWGEntity("LINE", "BEAM", None, {"length": 6.0, "text": "beam"})
    manifest = build_actual_ai_takeoff([row], source_fingerprint="sha256:drawing-A")
    assert manifest.status == "blocked"
    assert "one or more drawing entities have no stable source identity" in manifest.issues


def test_ambiguous_or_empty_evidence_fails_closed():
    row = entity(layer="WALL_BEAM", data={"area": 10.0, "length": 4.0})
    manifest = build_actual_ai_takeoff([row], source_fingerprint="sha256:drawing-A")
    assert manifest.status == "blocked"
    assert "no unambiguous quantity candidates were evidenced" in manifest.issues


def test_duplicate_source_identity_fails_closed():
    rows = [
        entity("same-source", data={"length": 6.0}),
        entity("same-source", data={"length": 3.0}),
    ]
    manifest = build_actual_ai_takeoff(rows, source_fingerprint="sha256:drawing-A")
    assert manifest.status == "blocked"
    assert "duplicate source identity across AI candidates" in manifest.issues


def test_low_confidence_is_blocked_by_production_gate():
    manifest = build_actual_ai_takeoff(
        [entity()], source_fingerprint="sha256:drawing-A", minimum_confidence=0.90
    )
    assert manifest.status == "blocked"
    assert manifest.fail_closed is True


def test_tampered_manifest_is_rejected():
    manifest = build_actual_ai_takeoff([entity()], source_fingerprint="sha256:drawing-A")
    tampered = replace(manifest, approved=True)
    ok, errors = validate_actual_ai_takeoff(tampered)
    assert not ok
    assert "automatic approval is forbidden" in errors
    assert "manifest fingerprint mismatch" in errors


def test_missing_source_fingerprint_is_rejected():
    with pytest.raises(ValueError):
        build_actual_ai_takeoff([entity()], source_fingerprint=" ")
