"""Offline cost breakdown and commercial factors."""
from __future__ import annotations
from typing import Iterable, Any

def cost_breakdown(rows: Iterable[Any], factors: dict[str,float] | None = None) -> dict[str,Any]:
    factors=factors or {}
    base=0.0; by_group={}; by_code={}
    for r in rows:
        d=r if isinstance(r,dict) else vars(r)
        amount=float(d.get("total") or (float(d.get("quantity",0) or 0)*float(d.get("unit_price",0) or 0)))
        group=str(d.get("group") or "سایر"); code=str(d.get("price_code") or "بدون کد")
        base += amount
        by_group[group]=by_group.get(group,0)+amount
        by_code[code]=by_code.get(code,0)+amount
    applied={}
    subtotal=base
    for name, rate in factors.items():
        rate=float(rate)
        delta=subtotal*rate
        applied[name]=delta
        subtotal += delta
    return {"base":base,"factors":applied,"grand_total":subtotal,
            "by_group":by_group,"by_code":by_code}
