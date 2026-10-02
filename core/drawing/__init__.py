"""Drawing intelligence primitives for extracting auditable engineering elements.

The layer is source-agnostic: CAD/PDF/BIM adapters can feed normalized primitives,
while downstream quantity/BOQ modules consume classified engineering elements.
"""
from .models import DrawingPrimitive, EngineeringElement
from .intelligence import DrawingIntelligence, classify_primitives
from .takeoff import drawing_takeoff

__all__ = [
    "DrawingPrimitive",
    "EngineeringElement",
    "DrawingIntelligence",
    "classify_primitives",
    "drawing_takeoff",
]
