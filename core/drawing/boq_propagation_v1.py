"""Deterministic BOQ propagation and revision-impact layer for P171-P180."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping, Sequence

@dataclass(frozen=True)
class BOQLineage:
    boq_id: str
    quantity_id: str
    element_id: str
    source_ids: tuple[str, ...]
    description: str
    quantity: float
    unit: str
    status: str = "accepted"
    def validate(self):
        if not all(x.strip() for x in (self.boq_id,self.quantity_id,self.element_id,self.description,self.unit)):
            raise ValueError("complete BOQ lineage is required")
        if self.quantity < 0:
            raise ValueError("quantity cannot be negative")
        if self.status not in {"accepted","review","rejected"}:
            raise ValueError("invalid BOQ status")
        if self.status == "accepted" and not self.source_ids:
            raise ValueError("accepted BOQ line requires source identity")
        return self

@dataclass(frozen=True)
class BOQImpact:
    boq_id: str
    element_id: str
    changed_fields: tuple[str, ...]
    old_quantity: float | None
    new_quantity: float | None
    impact: str
    def validate(self):
        if self.impact not in {"unchanged","quantity_changed","description_changed","unit_changed","review_required","removed"}:
            raise ValueError("invalid BOQ impact")
        return self

class BOQPropagationWorkflow:
    def __init__(self, *, accept_confidence: float = .80):
        if not 0 <= accept_confidence <= 1: raise ValueError("invalid confidence threshold")
        self.accept_confidence=accept_confidence

    @staticmethod
    def _id(*parts: object) -> str:
        return "boq-"+sha256("|".join(str(x).strip() for x in parts).encode()).hexdigest()[:16]

    def build(self, quantities: Sequence[object], rows: Sequence[Mapping[str,object]]) -> tuple[BOQLineage,...]:
        qmap={str(q.quantity_id):q for q in quantities}
        out=[]
        for row in rows:
            q=qmap.get(str(row.get("quantity_id","")))
            if q is None: continue
            status=str(row.get("status",getattr(q,"status","rejected")))
            quantity=row.get("quantity",getattr(q,"quantity",None))
            unit=str(row.get("unit",getattr(q,"unit",""))).strip()
            source_ids=tuple(getattr(q,"source_ids",()))
            confidence=float(row.get("confidence",getattr(q,"confidence",0)))
            if quantity is None or not unit or not source_ids: status="rejected"
            elif confidence < self.accept_confidence: status="review"
            line=BOQLineage(self._id(q.quantity_id,row.get("description",""),quantity,unit),
                q.quantity_id,q.element_id,source_ids,str(row.get("description","")).strip(),
                float(quantity or 0),unit,status)
            out.append(line.validate())
        return tuple(sorted(out,key=lambda x:x.boq_id))

    @staticmethod
    def impact(old: Sequence[BOQLineage], new: Sequence[BOQLineage]) -> tuple[BOQImpact,...]:
        a={x.boq_id:x for x in old}; b={x.boq_id:x for x in new}; out=[]
        for k in sorted(set(a)|set(b)):
            x,y=a.get(k),b.get(k)
            if x is None:
                out.append(BOQImpact(k,y.element_id,("presence",),None,y.quantity,"review_required")); continue
            if y is None:
                out.append(BOQImpact(k,x.element_id,("presence",),x.quantity,None,"removed")); continue
            changed=[]
            if x.quantity!=y.quantity: changed.append("quantity")
            if x.description!=y.description: changed.append("description")
            if x.unit!=y.unit: changed.append("unit")
            if x.source_ids!=y.source_ids: changed.append("source_ids")
            if x.status!=y.status: changed.append("status")
            if "source_ids" in changed: imp="review_required"
            elif "quantity" in changed: imp="quantity_changed"
            elif "description" in changed: imp="description_changed"
            elif "unit" in changed: imp="unit_changed"
            elif "status" in changed: imp="review_required"
            else: imp="unchanged"
            out.append(BOQImpact(k,y.element_id,tuple(changed),x.quantity,y.quantity,imp).validate())
        return tuple(out)
