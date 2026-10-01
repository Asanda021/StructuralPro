from __future__ import annotations
from typing import Any, Iterable

def build_boq(rows: Iterable[Any]) -> list[dict[str,Any]]:
    out=[]
    for r in rows:
        d=dict(r) if isinstance(r,dict) else {"description":getattr(r,"description",""),"quantity":getattr(r,"quantity",0),"unit":getattr(r,"unit",""),"price_code":getattr(r,"price_code",None),"unit_price":getattr(r,"unit_price",None),"total":getattr(r,"total",None)}
        if d.get("total") is None and d.get("unit_price") is not None: d["total"]=float(d.get("quantity",0))*float(d["unit_price"])
        out.append(d)
    return out
