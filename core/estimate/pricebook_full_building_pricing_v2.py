from __future__ import annotations
from dataclasses import dataclass
from core.estimate.item_code_normalization_v1 import code_key
DISCIPLINES=("ابنیه","تاسیسات مکانیکی","تاسیسات برقی","مرمت بناهای تاریخی")
@dataclass(frozen=True)
class ProductionRow:
    year:int; discipline:str; item_code:str; description:str; unit:str; unit_price:float; source_sha256:str; source_file:str
def normalize_rows(rows):
    out=[]
    for r in rows:
        code,unit=code_key(r.item_code,r.unit)
        if not code or not unit or not r.description or float(r.unit_price)<0 or not r.source_sha256: raise ValueError("invalid production pricebook row")
        if r.discipline not in DISCIPLINES: raise ValueError("unsupported building discipline")
        out.append(ProductionRow(int(r.year),r.discipline,code,r.description,unit,float(r.unit_price),r.source_sha256,r.source_file))
    return tuple(out)
def price_full_building(takeoff_rows,pricebook_rows,year,discipline):
    rows=normalize_rows(pricebook_rows); index={}
    for r in rows:
        if r.year==year and r.discipline==discipline:
            k=code_key(r.item_code,r.unit)
            if k in index and index[k].unit_price!=r.unit_price: raise ValueError("conflicting code/unit price")
            index[k]=r
    if not index: raise ValueError("pricebook discipline/year dataset is empty")
    priced=[]; unresolved=[]
    for item in takeoff_rows:
        row=index.get(code_key(item.get("item_code"),item.get("unit")))
        if row is None: unresolved.append(str(item.get("takeoff_id",""))); continue
        qty=float(item["quantity"])
        if qty<0: raise ValueError("negative takeoff quantity")
        priced.append({"takeoff_id":str(item["takeoff_id"]),"year":year,"discipline":discipline,"item_code":row.item_code,"unit":row.unit,"quantity":qty,"unit_price":row.unit_price,"total":qty*row.unit_price,"source_sha256":row.source_sha256,"source_file":row.source_file})
    if unresolved: raise ValueError("unresolved production pricebook rows: "+",".join(unresolved))
    return tuple(priced)
