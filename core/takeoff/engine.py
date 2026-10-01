"""Unified offline-first quantity takeoff engine.

Stage 1: one normalized interface for all current construction domains.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Iterable
from .modules import calculate_building_item, calculate_mechanical_item, calculate_electrical_item, calculate_civil_item
from .modules.advanced import calculate_advanced_item

@dataclass(frozen=True)
class TakeoffRow:
    domain: str
    item: str
    description: str
    quantity: float
    unit: str
    formula: str
    source: str = "manual"
    price_code: str | None = None
    warning: str = ""
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class TakeoffEngine:
    DOMAINS = ("building","mechanical","electrical","civil","advanced")
    def calculate(self, domain: str, item: str, *, description: str = "", source: str = "manual",
                  price_code: str | None = None, **params: Any) -> TakeoffRow:
        d=domain.strip().casefold()
        if d=="building": result=calculate_building_item(item,**params)
        elif d=="mechanical": result=calculate_mechanical_item(item,**params)
        elif d=="electrical": result=calculate_electrical_item(item,**params)
        elif d=="civil": result=calculate_civil_item(item,**params)
        elif d=="advanced": result=calculate_advanced_item(item,**params)
        else: raise KeyError(f"unsupported takeoff domain: {domain}")
        return TakeoffRow(d,item,description or item,float(result.quantity),result.unit,result.formula,
                          source,price_code,";".join(getattr(result,"warnings",()) or ()))
    def batch(self, rows: Iterable[dict[str,Any]]) -> list[TakeoffRow]:
        out=[]
        for row in rows:
            data=dict(row); domain=data.pop("domain"); item=data.pop("item")
            out.append(self.calculate(domain,item,description=data.pop("description",""),
                                      source=data.pop("source","manual"),
                                      price_code=data.pop("price_code",None),**data))
        return out
    @staticmethod
    def summarize(rows: Iterable[TakeoffRow]) -> dict[str,Any]:
        rows=list(rows); by_unit={}; by_domain={}
        for row in rows:
            by_unit[row.unit]=by_unit.get(row.unit,0.0)+row.quantity
            by_domain[row.domain]=by_domain.get(row.domain,0.0)+row.quantity
        return {"row_count":len(rows),"quantity_by_unit":by_unit,"quantity_by_domain":by_domain,
                "warnings":[r.to_dict() for r in rows if r.warning]}
