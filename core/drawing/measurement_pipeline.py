"""P80/P81 measurement-aware drawing pipeline with an explicit unit/scale gate."""
from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from .adapters import AdapterResult, DrawingAdapterRegistry
from .intelligence import DrawingIntelligence
from .measurement import primitive_measurements, scale_from_metadata


class DrawingMeasurementGate:
    """Resolve drawing scale and apply audited measurements to classified elements.

    The gate is deliberately fail-closed: without an explicit unit/scale, no
    engineering geometry is promoted into measurable quantities.
    """

    def __init__(self, adapters=None):
        self.adapters = adapters or DrawingAdapterRegistry()
        self.intelligence = DrawingIntelligence()

    def resolve_scale(
        self,
        metadata: Mapping[str, object],
        *,
        unit: str | None = None,
        scale_denominator: float = 1.0,
    ):
        if unit:
            from .measurement import scale_from_unit

            return scale_from_unit(unit, scale_denominator)
        return scale_from_metadata(metadata)

    def apply(
        self,
        adapted: AdapterResult,
        *,
        unit: str | None = None,
        scale_denominator: float = 1.0,
    ):
        scale = self.resolve_scale(
            adapted.source.metadata,
            unit=unit,
            scale_denominator=scale_denominator,
        )
        if scale is None:
            return scale, (), (
                "واحد یا مقیاس نقشه مشخص نیست؛ اندازه‌گیری مهندسی و متره خودکار انجام نشد",
            )

        measurements = primitive_measurements(adapted.primitives, scale)
        by_source = {m.source_ids[0]: m for m in measurements if m.source_ids}
        elements = []
        for element in self.intelligence.classify(adapted.primitives):
            measurement = next(
                (by_source[s] for s in element.source_ids if s in by_source),
                None,
            )
            if measurement is None:
                elements.append(element)
                continue

            geometry = dict(element.geometry)
            if "length" in geometry:
                geometry["length"] = measurement.value
                geometry["measurement_unit"] = measurement.unit
            elif "width" in geometry:
                geometry["width"] = measurement.value
                geometry["measurement_unit"] = measurement.unit
            properties = dict(element.properties)
            properties["measurement_formula"] = measurement.formula
            elements.append(replace(element, geometry=geometry, properties=properties))

        return scale, tuple(elements), ()

    def measure(
        self,
        path: str,
        *,
        unit: str | None = None,
        scale_denominator: float = 1.0,
    ):
        adapted = self.adapters.read(path)
        scale, elements, warnings = self.apply(
            adapted,
            unit=unit,
            scale_denominator=scale_denominator,
        )
        return adapted, scale, elements, warnings
