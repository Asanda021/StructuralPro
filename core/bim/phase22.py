"""Phase 22 IFC/BIM quantity bridge.

Provides a deterministic IFC ingestion boundary and maps model elements to
takeoff quantities without inventing missing geometry or properties.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping
import hashlib
import json


class IFCError(ValueError):
    pass


@dataclass(frozen=True)
class IFCElement:
    global_id: str
    ifc_type: str
    name: str
    properties: tuple[tuple[str, str], ...]
    quantities: tuple[tuple[str, float], ...]
    source: str = "ifc"


@dataclass(frozen=True)
class IFCModel:
    schema: str
    project_name: str
    units: str
    elements: tuple[IFCElement, ...]
    source_fingerprint: str

    @property
    def element_count(self) -> int:
        return len(self.elements)

    def by_type(self, ifc_type: str) -> tuple[IFCElement, ...]:
        return tuple(e for e in self.elements if e.ifc_type == ifc_type)

    def quantity_totals(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for element in self.elements:
            for key, value in element.quantities:
                totals[key] = totals.get(key, 0.0) + value
        return {k: round(v, 12) for k, v in sorted(totals.items())}

    def export_payload(self) -> dict[str, Any]:
        return {
            "schema": "structuralpro.ifc.bim.v1",
            "ifc_schema": self.schema,
            "project_name": self.project_name,
            "units": self.units,
            "element_count": self.element_count,
            "elements": [asdict(e) for e in self.elements],
            "quantity_totals": self.quantity_totals(),
            "source_fingerprint": self.source_fingerprint,
        }


def fingerprint(payload: bytes) -> str:
    if not isinstance(payload, bytes) or not payload:
        raise IFCError("IFC artifact must be non-empty bytes")
    return hashlib.sha256(payload).hexdigest()


def _prop_value(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True, default=str)


def _extract_element(entity: Any) -> IFCElement:
    gid = str(getattr(entity, "GlobalId", "") or "")
    if not gid:
        raise IFCError("IFC element without GlobalId")
    props: list[tuple[str, str]] = []
    quantities: list[tuple[str, float]] = []
    for definition in getattr(entity, "IsDefinedBy", ()) or ():
        pset = getattr(definition, "RelatingPropertyDefinition", None)
        for prop in getattr(pset, "HasProperties", ()) or ():
            name = str(getattr(prop, "Name", "") or "")
            value = getattr(prop, "NominalValue", None)
            value = getattr(value, "wrappedValue", value)
            if name:
                props.append((name, _prop_value(value)))
    for definition in getattr(entity, "IsDefinedBy", ()) or ():
        qset = getattr(definition, "RelatingPropertyDefinition", None)
        for quantity in getattr(qset, "Quantities", ()) or ():
            name = str(getattr(quantity, "Name", "") or "")
            for field in ("LengthValue", "AreaValue", "VolumeValue", "CountValue", "WeightValue"):
                value = getattr(quantity, field, None)
                if value is not None and name:
                    quantities.append((name, float(value)))
                    break
    return IFCElement(
        global_id=gid,
        ifc_type=str(entity.is_a()),
        name=str(getattr(entity, "Name", "") or ""),
        properties=tuple(sorted(props)),
        quantities=tuple(sorted(quantities)),
    )


def extract_ifc(payload: bytes) -> IFCModel:
    if not isinstance(payload, bytes) or not payload:
        raise IFCError("IFC artifact must be non-empty bytes")
    try:
        import ifcopenshell
        model = ifcopenshell.open(payload) if isinstance(payload, str) else ifcopenshell.file.from_string(payload.decode("utf-8"))
        # Some parser versions return a file without a loaded schema instead of
        # raising for malformed STEP input. Resolve it inside the decoding gate.
        schema = str(model.schema)
        if not schema:
            raise IFCError("IFC schema unresolved")
        projects = model.by_type("IfcProject")
        products = model.by_type("IfcProduct")
    except Exception as exc:
        raise IFCError("IFC decoding failed") from exc

    project = next(iter(projects), None)
    units = "unresolved"
    if project is not None:
        assignments = getattr(project, "UnitsInContext", None)
        if assignments and getattr(assignments, "Units", None):
            names = [str(getattr(u, "Name", "")) for u in assignments.Units]
            units = ",".join(sorted(x for x in names if x)) or "unresolved"
    elements = []
    for entity in products:
        if entity.is_a("IfcProject") or entity.is_a("IfcSite"):
            continue
        try:
            elements.append(_extract_element(entity))
        except IFCError:
            continue
    elements.sort(key=lambda e: (e.ifc_type, e.global_id))
    return IFCModel(
        schema=schema,
        project_name=str(getattr(project, "Name", "") if project else ""),
        units=units,
        elements=tuple(elements),
        source_fingerprint=fingerprint(payload),
    )


def validate_model(model: IFCModel) -> None:
    if not model.schema:
        raise IFCError("IFC schema unresolved")
    if model.units == "unresolved":
        raise IFCError("IFC units unresolved")
    ids = [e.global_id for e in model.elements]
    if len(ids) != len(set(ids)):
        raise IFCError("Duplicate IFC GlobalId detected")


def element_to_takeoff(model: IFCModel) -> list[dict[str, Any]]:
    validate_model(model)
    return [
        {
            "element_id": e.global_id,
            "element_type": e.ifc_type,
            "name": e.name,
            "quantities": dict(e.quantities),
            "source": "IFC",
        }
        for e in model.elements
    ]
