"""Deterministic CAD geometry -> auto-takeoff extraction.

The extractor turns already-parsed CAD entities into auditable candidates.
It never guesses missing geometry and keeps the CAD handle/layer as provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from core.drawings.element_recognition import enrich_candidate


_LENGTH_TYPES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC"}
_AREA_TYPES = {"LWPOLYLINE", "POLYLINE", "CIRCLE"}


@dataclass(frozen=True)
class GeometryTakeoffCandidate:
    source: str
    entity_type: str
    layer: str
    handle: str | None
    metric: str
    quantity: float
    unit: str
    confidence: float
    needs_confirmation: bool = True
    description: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "description": self.description or self.layer or self.entity_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "entity_type": self.entity_type,
            "layer": self.layer,
            "handle": self.handle,
            "metric": self.metric,
            "confidence": self.confidence,
            "needs_confirmation": self.needs_confirmation,
        }


def _finite_nonnegative(value: Any, *, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid CAD {field}") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"Invalid CAD {field}")
    return number


def _source(entity: Any, index: int) -> str:
    layer = str(getattr(entity, "layer", "") or "0")
    handle = getattr(entity, "handle", None)
    if handle:
        return f"cad:{layer}:{handle}"
    return f"cad:{layer}:entity-{index}"


def extract_geometry_candidates(
    entities: list[Any],
    *,
    include_count: bool = True,
    confidence: float = 0.98,
    source_unit: str = "m",
) -> list[dict[str, Any]]:
    """Extract one candidate per source entity, with deterministic de-duplication.

    Length/area are preferred over count. INSERT and other non-measured entities
    become count candidates when requested. A real CAD handle is the identity;
    handle-less entities use a stable input-position fallback.
    """
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    source_unit = str(source_unit or "unknown").lower()
    if source_unit not in {"m", "unknown", "unitless"}:
        raise ValueError(f"unsupported CAD source unit: {source_unit}")

    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for index, entity in enumerate(entities, 1):
        entity_type = str(getattr(entity, "entity_type", "") or "").upper()
        layer = str(getattr(entity, "layer", "") or "0")
        handle = getattr(entity, "handle", None)
        source = _source(entity, index)
        if source in seen:
            continue
        seen.add(source)

        data = getattr(entity, "data", {}) or {}
        metric: str | None = None
        unit: str | None = None
        quantity: float | None = None

        if entity_type in _AREA_TYPES and data.get("area") is not None:
            quantity = _finite_nonnegative(data.get("area"), field="area")
            metric, unit = "area", "m2"
        elif entity_type in _LENGTH_TYPES and data.get("length") is not None:
            quantity = _finite_nonnegative(data.get("length"), field="length")
            metric, unit = "length", "m"
        elif include_count:
            quantity, metric, unit = 1.0, "count", "عدد"

        if quantity is None:
            continue

        candidate = GeometryTakeoffCandidate(
            source=source,
            entity_type=entity_type,
            layer=layer,
            handle=str(handle) if handle is not None else None,
            metric=metric,
            quantity=quantity,
            unit=unit if source_unit == "m" else "unknown",
            confidence=confidence if source_unit == "m" else min(confidence, 0.5),
            description=layer or entity_type,
        )
        out.append(enrich_candidate(entity, candidate.as_dict()))

    return out


def aggregate_geometry_candidates(
    entities: list[Any],
    *,
    confidence: float = 0.98,
    source_unit: str = "m",
) -> list[dict[str, Any]]:
    """Aggregate measured geometry by layer + metric without losing provenance."""
    candidates = extract_geometry_candidates(entities, confidence=confidence, source_unit=source_unit)
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}

    for row in candidates:
        key = (row["layer"], row["metric"], row["unit"])
        group = groups.setdefault(
            key,
            {
                "source": f"cad-geometry:{row['layer']}:{row['metric']}",
                "description": row["layer"] or row["entity_type"],
                "quantity": 0.0,
                "unit": row["unit"],
                "metric": row["metric"],
                "layer": row["layer"],
                "confidence": min(float(row["confidence"]), 1.0),
                "needs_confirmation": True,
                "entity_count": 0,
                "source_entities": [],
            },
        )
        group["quantity"] += row["quantity"]
        group["entity_count"] += 1
        group["source_entities"].append(row["source"])

    return list(groups.values())
