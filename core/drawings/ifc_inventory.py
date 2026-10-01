"""Deeper local IFC inventory and mapping helpers."""
from __future__ import annotations
from typing import Any, Iterable

def inventory(rows:Iterable[dict[str,Any]])->dict[str,Any]:
    rows=list(rows); by_type={}; by_level={}; quantity_totals={}
    for r in rows:
        typ=str(r.get("ifc_type") or "Unknown"); by_type[typ]=by_type.get(typ,0)+1
        props=r.get("properties") or {}
        level=str(props.get("Level") or props.get("Storey") or r.get("level") or "بدون طبقه")
        by_level[level]=by_level.get(level,0)+1
        for k,v in (r.get("quantities") or {}).items():
            try: quantity_totals[k]=quantity_totals.get(k,0)+float(v)
            except (TypeError,ValueError): pass
    return {"objects":len(rows),"by_type":by_type,"by_level":by_level,"quantity_totals":quantity_totals}

def normalize_bim_rows(rows:Iterable[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for r in rows:
        q=r.get("quantities") or {}
        out.append({
            "global_id":str(r.get("global_id") or ""),
            "ifc_type":str(r.get("ifc_type") or ""),
            "name":str(r.get("name") or ""),
            "level":str((r.get("properties") or {}).get("Level") or r.get("level") or ""),
            "quantities":{str(k):float(v) for k,v in q.items() if isinstance(v,(int,float))},
        })
    return out

def map_bim_to_price(rows:Iterable[dict[str,Any]], mapping:dict[str,str])->list[dict[str,Any]]:
    out=[]
    for r in rows:
        code=mapping.get(r.get("ifc_type")) or mapping.get("default")
        if code: out.append({**r,"price_code":code})
    return out
