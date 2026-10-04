"""P84 — deterministic pricebook mapping by item code and unit."""
from dataclasses import dataclass
from core.estimate.pricebook_ingestion_v1 import PriceRow

@dataclass(frozen=True)
class CodeUnitMatch:
    takeoff_id:str
    item_code:str
    unit:str
    exact:bool

def index_code_unit(rows, year, discipline):
    selected=[r for r in rows if r.year==year and r.discipline==discipline and r.item_code and r.unit and r.unit_price is not None]
    index={}
    for r in selected:
        key=(r.item_code.strip(),r.unit.strip())
        if key in index and index[key].rate != r.unit_price:
            raise ValueError("conflicting rates for item code/unit")
        index[key]=PriceRow(r.year,"",r.item_code,r.description,r.unit,r.unit_price,"IRR")
    return index

def map_by_code_unit(takeoff_rows, rows, year, discipline):
    index=index_code_unit(rows,year,discipline)
    matches=[]
    unresolved=[]
    for item in takeoff_rows:
        key=(str(item.get("item_code","")).strip(),str(item.get("unit","")).strip())
        if key in index:
            matches.append(CodeUnitMatch(str(item["takeoff_id"]),key[0],key[1],True))
        else:
            unresolved.append(str(item["takeoff_id"]))
    return {"matches":matches,"unresolved":unresolved,"green":not unresolved,"count":len(matches)}
