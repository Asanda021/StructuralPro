"""P80 measurement-aware drawing pipeline with an explicit unit/scale gate."""
from __future__ import annotations
from typing import Mapping
from .adapters import DrawingAdapterRegistry
from .intelligence import DrawingIntelligence
from .measurement import primitive_measurements, scale_from_metadata

class DrawingMeasurementGate:
    def __init__(self, adapters=None):
        self.adapters=adapters or DrawingAdapterRegistry()
        self.intelligence=DrawingIntelligence()
    def resolve_scale(self, metadata: Mapping[str,object], *, unit=None, scale_denominator=1.0):
        if unit:
            from .measurement import scale_from_unit
            return scale_from_unit(unit,scale_denominator)
        return scale_from_metadata(metadata)
    def measure(self,path: str,*,unit=None,scale_denominator=1.0):
        adapted=self.adapters.read(path)
        scale=self.resolve_scale(adapted.source.metadata,unit=unit,scale_denominator=scale_denominator)
        if scale is None:
            return adapted,None,(),("واحد یا مقیاس نقشه مشخص نیست؛ اندازه‌گیری مهندسی انجام نشد",)
        measurements=primitive_measurements(adapted.primitives,scale)
        by_source={m.source_ids[0]:m for m in measurements if m.source_ids}
        elements=[]
        for element in self.intelligence.classify(adapted.primitives):
            measurement=next((by_source[s] for s in element.source_ids if s in by_source),None)
            if measurement is None:
                elements.append(element); continue
            geometry=dict(element.geometry)
            if "length" in geometry: geometry.update(length=measurement.value,measurement_unit="m")
            elif "width" in geometry: geometry.update(width=measurement.value,measurement_unit="m")
            from dataclasses import replace
            elements.append(replace(element,geometry=geometry))
        return adapted,scale,tuple(elements),()
