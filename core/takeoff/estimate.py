"""Deterministic estimate pipeline: BOQ lines plus configurable commercial factors."""
from __future__ import annotations
from typing import Iterable, Any
from core.takeoff.boq import build_boq, boq_summary
from core.takeoff.costing import cost_breakdown

def build_estimate(rows:Iterable[Any], *, factors=None, aggregate=True)->dict[str,Any]:
    boq=build_boq(rows,aggregate=aggregate)
    cost=cost_breakdown(boq,factors or {})
    return {"boq":boq,"summary":boq_summary(boq),"cost":cost}

def compare_estimates(old:dict[str,Any], new:dict[str,Any])->dict[str,float]:
    a=float(old.get("cost",{}).get("grand_total",0)); b=float(new.get("cost",{}).get("grand_total",0))
    return {"old_total":a,"new_total":b,"delta":b-a,"delta_percent":0.0 if a==0 else (b-a)/a*100}
