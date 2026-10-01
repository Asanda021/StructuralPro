"""Unified drawing -> quantity -> price -> BOQ pipeline.
All steps are deterministic and can run offline.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable

@dataclass(frozen=True)
class PipelineRow:
    source: str
    description: str
    quantity: float
    unit: str
    price_code: str | None = None
    unit_price: float | None = None
    total: float | None = None

class DrawingTakeoffPipeline:
    def __init__(self, price_resolver=None):
        self.price_resolver = price_resolver

    def normalize(self, rows: Iterable[dict[str, Any]]) -> list[PipelineRow]:
        out=[]
        for r in rows:
            q=float(r.get("quantity",0))
            unit=str(r.get("unit","")).strip()
            code=r.get("price_code")
            price=None
            total=None
            if code and self.price_resolver:
                price=float(self.price_resolver(code) or 0)
                total=q*price
            out.append(PipelineRow(str(r.get("source","drawing")),str(r.get("description","")),q,unit,code,price,total))
        return out

    def aggregate(self, rows: Iterable[PipelineRow]) -> list[PipelineRow]:
        groups={}
        for r in rows:
            key=(r.price_code or r.description,r.unit)
            old=groups.get(key)
            if old is None: groups[key]=r
            else:
                q=old.quantity+r.quantity
                total=None if old.unit_price is None else q*old.unit_price
                groups[key]=PipelineRow(old.source,old.description,q,old.unit,old.price_code,old.unit_price,total)
        return list(groups.values())

    def to_boq(self, rows: Iterable[PipelineRow]) -> list[dict[str,Any]]:
        return [{"source":r.source,"description":r.description,"quantity":r.quantity,"unit":r.unit,
                 "price_code":r.price_code,"unit_price":r.unit_price,"total":r.total} for r in rows]
