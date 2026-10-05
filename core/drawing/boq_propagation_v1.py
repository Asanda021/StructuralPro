"""Deterministic BOQ propagation and revision-impact layer for P171-P180."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping, Sequence

@dataclass(frozen=True)
class BOQLineage:
    boq_id:str; quantity_id:str; element_id:str; source_ids:tuple[str,...]; description:str; quantity:float; unit:str; status:str="accepted"
    def validate(self):
        if not all(x.strip() for x in (self.boq_id,self.quantity_id,self.element_id,self.description,self.unit)): raise ValueError("complete BOQ lineage is required")
        if self.quantity<0: raise ValueError("quantity cannot be negative")
        if self.status not in {"accepted","review","rejected"}: raise ValueError("invalid BOQ status")
        if self.status=="accepted" and not self.source_ids: raise ValueError("accepted BOQ line requires source identity")
        return self

@dataclass(frozen=True)
class BOQImpact:
    boq_id:str; element_id:str; changed_fields:tuple[str,...]; old_quantity:float|None; new_quantity:float|None; impact:str
    def validate(self):
        if self.impact not in {"unchanged","quantity_changed","description_changed","unit_changed","review_required","removed"}: raise ValueError("invalid BOQ impact")
        return self

class BOQPropagationWorkflow:
    def __init__(self,*,accept_confidence=.80):
        if not 0<=accept_confidence<=1: raise ValueError("invalid confidence threshold")
        self.accept_confidence=accept_confidence
    @staticmethod
    def _id(*parts): return "boq-"+sha256("|".join(str(x).strip() for x in parts).encode()).hexdigest()[:16]
    def build(self,quantities:Sequence[object],rows:Sequence[Mapping[str,object]]):
        qmap={str(q.quantity_id):q for q in quantities}; out=[]; seen=set()
        for row in rows:
            q=qmap.get(str(row.get("quantity_id","")))
            if q is None: continue
            desc=str(row.get("description","")).strip(); qty=row.get("quantity",getattr(q,"quantity",None)); unit=str(row.get("unit",getattr(q,"unit",""))).strip()
            src=tuple(sorted(set(getattr(q,"source_ids",())))); conf=float(row.get("confidence",getattr(q,"confidence",0))); status=str(row.get("status",getattr(q,"status","rejected")))
            if qty is None or not unit or not src or not desc: status="rejected"
            elif conf<self.accept_confidence: status="review"
            line=BOQLineage(self._id(q.quantity_id,desc,unit),q.quantity_id,q.element_id,src,desc,float(qty or 0),unit,status)
            if line.boq_id in seen: raise ValueError("duplicate BOQ identity")
            seen.add(line.boq_id); out.append(line.validate())
        return tuple(sorted(out,key=lambda x:x.boq_id))
    @staticmethod
    def impact(old,new):
        a={x.boq_id:x for x in old}; b={x.boq_id:x for x in new}; out=[]
        for k in sorted(set(a)|set(b)):
            x,y=a.get(k),b.get(k)
            if x is None: out.append(BOQImpact(k,y.element_id,("presence",),None,y.quantity,"review_required")); continue
            if y is None: out.append(BOQImpact(k,x.element_id,("presence",),x.quantity,None,"removed")); continue
            ch=[]; ch += ["quantity"] if x.quantity!=y.quantity else []; ch += ["description"] if x.description!=y.description else []; ch += ["unit"] if x.unit!=y.unit else []; ch += ["source_ids"] if x.source_ids!=y.source_ids else []; ch += ["status"] if x.status!=y.status else []
            imp="review_required" if ("source_ids" in ch or "status" in ch) else ("quantity_changed" if "quantity" in ch else "description_changed" if "description" in ch else "unit_changed" if "unit" in ch else "unchanged")
            out.append(BOQImpact(k,y.element_id,tuple(ch),x.quantity,y.quantity,imp).validate())
        return tuple(out)
    @staticmethod
    def fingerprints(lines):
        return tuple(sorted("line-"+sha256("|".join((x.boq_id,x.quantity_id,x.element_id,x.description,str(x.quantity),x.unit,x.status,*x.source_ids)).encode()).hexdigest()[:16] for x in lines))
    @staticmethod
    def unresolved(lines): return tuple(x for x in lines if x.status!="accepted")
    @staticmethod
    def source_conflicts(lines):
        by={}
        for x in lines: by.setdefault(x.element_id,set()).update(x.source_ids)
        return tuple(sorted(e for e,s in by.items() if len(s)>1))
