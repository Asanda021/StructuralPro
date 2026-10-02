"""Professional estimate orchestration with explicit finalization gates."""
from __future__ import annotations
from typing import Iterable,Any
import math
from core.takeoff.boq import build_boq,validate_boq_structure,boq_summary
from core.takeoff.costing import cost_breakdown
def _num(value,name):
    x=float(value)
    if not math.isfinite(x) or x<0: raise ValueError(f"{name} must be finite and non-negative")
    return x
def _validate_factors(factors):
    out={}
    for name,value in (factors or {}).items():
        key=str(name).strip()
        if not key: raise ValueError("factor name cannot be empty")
        out[key]=_num(value,"factor rate")
    return out
def build_estimate(rows:Iterable[Any],*,factors=None,aggregate=True)->dict[str,Any]:
    normalized=_validate_factors(factors); boq=build_boq(rows,aggregate=aggregate); validation=validate_boq_structure(boq)
    cost=cost_breakdown(boq,normalized)
    return {"boq":boq,"summary":boq_summary(boq),"validation":validation,"cost":cost,"factors":normalized,"finalizable":bool(validation["valid"])}
