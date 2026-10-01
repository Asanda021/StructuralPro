"""Civil, site and road quantity operations."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class CivilResult:
    item: str
    quantity: float
    unit: str
    formula: str

def _n(v,name):
    try: x=float(v)
    except (TypeError,ValueError): raise ValueError(f"{name} must be numeric")
    if x<0: raise ValueError(f"{name} must be >= 0")
    return x

def calculate_civil_item(item: str, **p: Any) -> CivilResult:
    k=item.casefold().replace(" ","_")
    if k in {"excavation","خاکبرداری","خاک_برداری"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p["depth"],"depth"); return CivilResult("خاکبرداری",q,"m3","L×W×D")
    if k in {"backfill","خاکریزی","خاک_ریزی"}:
        q=max(0.0,_n(p["excavation"],"excavation")-_n(p.get("deductions",0),"deductions")); return CivilResult("خاکریزی",q,"m3","خاکبرداری−کسرها")
    if k in {"paving","concrete_yard","بتن_محوطه"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p["thickness"],"thickness"); return CivilResult("بتن محوطه",q,"m3","L×W×t")
    if k in {"asphalt","آسفالت"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p["thickness"],"thickness"); return CivilResult("آسفالت",q,"m3","L×W×t")
    if k in {"curb","جدول"}:
        q=_n(p["length"],"length")*_n(p.get("count",1),"count"); return CivilResult("جدول",q,"m","L×تعداد")
    if k in {"drainage","زهکشی"}:
        q=_n(p["length"],"length"); return CivilResult("زهکشی",q,"m","L")
    if k in {"fence_wall","wall","دیوارکشی"}:
        q=_n(p["length"],"length")*_n(p["height"],"height"); return CivilResult("دیوارکشی",q,"m2","L×H")
    raise KeyError(f"unsupported civil item: {item}")
