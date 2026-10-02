"""Operational source-to-BOQ drawing pipeline with measurement integrity."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from core.standards import StandardsEngine, default_iran_registry
from core.takeoff.drawing_pipeline import DrawingTakeoffPipeline
from .adapters import AdapterResult, DrawingAdapterRegistry
from .intelligence import DrawingIntelligence
from .takeoff import drawing_takeoff
from .measurement_pipeline import DrawingMeasurementGate

@dataclass(frozen=True)
class DrawingPipelineResult:
    source: Any
    adapter_warnings: tuple[str, ...]
    measurement_warnings: tuple[str, ...]
    scale: Any
    primitives: tuple
    elements: tuple
    quantity_candidates: tuple[dict, ...]
    standards: dict[str, tuple[dict, ...]]
    boq: tuple[dict, ...]

class DrawingIntelligencePipeline:
    """Run drawing source -> measured elements -> standards -> takeoff -> BOQ."""
    def __init__(self, adapters=None, standards_engine=None, price_resolver: Callable[[str], float | None] | None = None):
        self.adapters = adapters or DrawingAdapterRegistry()
        self.standards = standards_engine or StandardsEngine(default_iran_registry())
        self.takeoff_pipeline = DrawingTakeoffPipeline(price_resolver=price_resolver)
        self.intelligence = DrawingIntelligence()
        self.measurement_gate = DrawingMeasurementGate(self.adapters)

    @staticmethod
    def _standard_domain(domain: str) -> str:
        if domain == "foundations":
            return "foundations"
        if domain in {"concrete", "steel"}:
            return domain
        return domain

    def process(self, path: str, *, unit=None, scale_denominator=1.0) -> DrawingPipelineResult:
        adapted: AdapterResult = self.adapters.read(path)
        scale, elements, measurement_warnings = self.measurement_gate.apply(
            adapted, unit=unit, scale_denominator=scale_denominator
        )
        candidates = drawing_takeoff(elements) if scale is not None else ()

        standard_map: dict[str, tuple[dict, ...]] = {}
        for element in elements:
            domain = self._standard_domain(element.domain)
            try:
                decisions = self.standards.resolve(domain=domain)
            except (LookupError, ValueError):
                decisions = ()
            standard_map[element.element_id] = tuple({
                "rule_code": d.rule_code, "source_code": d.source_code,
                "source_title": d.source_title, "edition": d.edition,
                "clause": d.clause, "topic": d.topic, "requirement": d.requirement,
            } for d in decisions)

        rows = []
        for candidate in candidates:
            if candidate["quantity"] is None:
                continue
            source_ids = candidate["source_ids"]
            source = source_ids[0] if source_ids else candidate["element_id"]
            rows.append({
                "source": source,
                "description": f"{candidate['domain']}:{candidate['kind']}",
                "quantity": candidate["quantity"],
                "unit": candidate["unit"],
            })
        boq_rows = self.takeoff_pipeline.to_boq(self.takeoff_pipeline.normalize(rows))
        return DrawingPipelineResult(
            source=adapted.source,
            adapter_warnings=adapted.warnings,
            measurement_warnings=tuple(measurement_warnings),
            scale=scale,
            primitives=adapted.primitives,
            elements=elements,
            quantity_candidates=candidates,
            standards=standard_map,
            boq=tuple(boq_rows),
        )
