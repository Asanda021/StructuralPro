"""Deterministic production-release gate for StructuralPro."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping
REQUIRED_FIELDS=("version","commit","release_preparation_fingerprint","artifact_manifest","rollback_commit")
@dataclass(frozen=True)
class ProductionRelease:
    released: bool
    blockers: tuple[str,...]
    fingerprint: str
def evaluate_production_release(evidence: Mapping[str,object])->ProductionRelease:
    errors=[]
    if not isinstance(evidence,Mapping) or not evidence:
        errors.append("evidence must be a non-empty mapping"); canonical={}
    else:
        errors += [f"unknown field: {x}" for x in sorted(set(evidence)-set(REQUIRED_FIELDS))]
        errors += [f"missing field: {x}" for x in sorted(set(REQUIRED_FIELDS)-set(evidence))]
        canonical=dict(evidence)
        for k in ("version","commit","release_preparation_fingerprint","rollback_commit"):
            if k in evidence and (not isinstance(evidence[k],str) or not evidence[k].strip()):
                errors.append(f"{k} must be a non-empty string")
        manifest=evidence.get("artifact_manifest")
        if not isinstance(manifest,Mapping) or not manifest:
            errors.append("artifact_manifest must be a non-empty mapping")
        else:
            for name,digest in manifest.items():
                if not isinstance(name,str) or not name.strip(): errors.append("artifact name must be a non-empty string")
                if not isinstance(digest,str) or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest.lower()):
                    errors.append(f"{name} must be a lowercase SHA-256")
    fp=sha256(json.dumps(canonical,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    return ProductionRelease(not errors,tuple(sorted(set(errors))),fp)
def require_production_release(evidence):
    result=evaluate_production_release(evidence)
    if not result.released: raise ValueError("production release gate failed")
    return result
