"""Operational P79 source-to-BOQ pipeline.

Drawing Source -> Adapter -> Drawing Intelligence -> Engineering Elements ->
Standards/Domain -> Takeoff -> BOQ.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.standards import StandardsEngine, default_iran_registry
from core.takeoff.drawing_pipeline import DrawingTakeoffPipeline

from .adapters import AdapterResult, DrawingAdapterRegistry
from .intelligence import DrawingIntelligence
from .takeoff import drawing_takeoff


@dataclass(frozen=True)
class DrawingPipelineResult:
    source: Any
    adapter_warnings: tuple[str, ...]
    primitives: tuple
    elements: tuple
    quantity_candidates: tuple[dict, ...]
    standards: dict[str, tuple[dict, ...]]
    boq: tuple[dict, ...]


class DrawingIntelligencePipeline:
    """Runs one auditable drawing source through the canonical P78/P79 path."""

    def __init__(
        self,
        adapters: DrawingAdapterRegistry | None = None,
        standards_engine: StandardsEngine | None = None,
        price_resolver: Callable[[str], float | None] | None = None,
    ):
        self.adapters = adapters or DrawingAdapterRegistry()
        self.standards = standards_engine or StandardsEngine(default_iran_registry())
        self.takeoff_pipeline = DrawingTakeoffPipeline(price_resolver=price_resolver)
        self.intelligence = DrawingIntelligence()

    @staticmethod
    def _standard_domain(domain: str) -> str:
        if domain == "foundations":
            return "foundations"
        if domain in {"concrete", "steel"}:
            return domain
        return domain

    def process(self, path: str) -> DrawingPipelineResult:
        adapted: AdapterResult = self.adapters.read(path)
        elements = self.intelligence.classify(adapted.primitives)
        candidates = drawing_takeoff(elements)

        standard_map: dict[str, tuple[dict, ...]] = {}
        for element in elements:
            domain = self._standard_domain(element.domain)
            try:
                decisions = self.standards.resolve(domain=domain)
            except (LookupError, ValueError):
                decisions = ()
            standard_map[element.element_id] = tuple(
                {
                    "rule_code": d.rule_code,
                    "source_code": d.source_code,
                    "source_title": d.source_title,
                    "edition": d.edition,
                    "clause": d.clause,
                    "topic": d.topic,
                    "requirement": d.requirement,
                }
                for d in decisions
            )

        rows = []
        for candidate in candidates:
            if candidate["quantity"] is None:
                continue
            source_ids = candidate["source_ids"]
            source = source_ids[0] if source_ids else candidate["element_id"]
            rows.append(
                {
                    "source": source,
                    "description": f"{candidate['domain']}:{candidate['kind']}",
                    "quantity": candidate["quantity"],
                    "unit": candidate["unit"],
                }
            )
        boq_rows = self.takeoff_pipeline.to_boq(
            self.takeoff_pipeline.normalize(rows)
        )

        return DrawingPipelineResult(
            source=adapted.source,
            adapter_warnings=adapted.warnings,
            primitives=adapted.primitives,
            elements=elements,
            quantity_candidates=candidates,
            standards=standard_map,
            boq=tuple(boq_rows),
        )
