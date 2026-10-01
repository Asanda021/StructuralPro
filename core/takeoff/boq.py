"""Deterministic BOQ builder: normalize, validate, aggregate and total."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, Any
import math
from .units import normalize_unit

@dataclass(frozen=True)
class BOQLine:
    item_no: int
    source: str
    description: str
    quantity: float
    unit: str
    price_code: str | None = None
    unit_price: float | None = None
    total: float | None = None
    factor: float = 1.0
    warning: str = ""

def _read(r: Any, name: str, default=None):
    return r.get(name, default) if isinstance(r, dict) else getattr(r, name, default)

def build_boq(rows: Iterable[Any], aggregate: bool = True, factor: float = 1.0) -> list[dict[str, Any]]:
    if not math.isfinite(float(factor)) or float(factor) < 0:
        raise ValueError("factor must be finite and non-negative")
    raw=[]
    for r in rows:
        source=str(_read(r,"source","") or "").strip()
        q=float(_read(r,"quantity",0) or 0)
        if not math.isfinite(q) or q < 0:
            raise ValueError("quantity must be finite and non-negative")
        raw_unit=str(_read(r,"unit","") or "").strip()
        if not raw_unit:
            raise ValueError("unit is required")
        unit=normalize_unit(raw_unit)
        price=_read(r,"unit_price",None)
        price=None if price is None else float(price)
        if price is not None and (not math.isfinite(price) or price < 0):
            raise ValueError("unit_price must be finite and non-negative")
        code=_read(r,"price_code",None)
        desc=str(_read(r,"description","") or "").strip()
        f=float(_read(r,"factor",factor) or factor)
        if not math.isfinite(f) or f < 0:
            raise ValueError("factor must be finite and non-negative")
        total=None if price is None else round(q*price*f, 10)
        warning="" if q >= 0 and unit else "missing_quantity_or_unit"
        if price == 0: warning = (warning+";" if warning else "")+"zero_price"
        raw.append({"source":source, "description":desc,
                    "quantity":q, "unit":unit, "price_code":code, "unit_price":price,
                    "total":total, "factor":f, "warning":warning})
    if aggregate:
        groups={}
        for r in raw:
            key=(r["price_code"] or r["description"],r["unit"],r["unit_price"],r["factor"])
            if key not in groups: groups[key]=dict(r)
            else:
                groups[key]["quantity"] += r["quantity"]
                if r["total"] is not None: groups[key]["total"]=(groups[key]["total"] or 0)+r["total"]
        raw=list(groups.values())
    return [dict(item_no=i, **r) for i,r in enumerate(raw,1)]

def boq_summary(rows: Iterable[dict[str,Any]]) -> dict[str,Any]:
    rows=list(rows)
    return {
        "line_count": len(rows),
        "quantity_by_unit": _sum_by(rows, "unit", "quantity"),
        "amount_by_code": _sum_by(rows, "price_code", "total"),
        "grand_total": sum(float(r.get("total") or 0) for r in rows),
        "warnings": [r for r in rows if r.get("warning")]
    }

def _sum_by(rows, key, value):
    out={}
    for r in rows:
        k=r.get(key) or "بدون کد"
        out[k]=out.get(k,0)+float(r.get(value) or 0)
    return out
