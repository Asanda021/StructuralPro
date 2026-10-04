"""P78 — connect normalized pricebook rows to the canonical pricing engine."""
from dataclasses import dataclass
from core.estimate.pricebook_ingestion_v1 import PriceRow

@dataclass(frozen=True)
class IntegrationResult:
    accepted:tuple[PriceRow,...]
    rejected:int
    missing_rate:int
    fingerprint:str

def to_price_rows(rows):
    from hashlib import sha256
    accepted=[]; rejected=0; missing=0
    for r in rows:
        if not r.item_code or not r.description or not r.unit:
            rejected+=1; continue
        if r.unit_price is None:
            missing+=1; continue
        if r.unit_price < 0:
            rejected+=1; continue
        accepted.append(PriceRow(r.year,"",r.item_code,r.description,r.unit,r.unit_price,"IRR"))
    payload="|".join(sorted(f"{x.year}|{x.item_code}|{x.description}|{x.unit}|{x.rate}" for x in accepted))
    return IntegrationResult(tuple(accepted),rejected,missing,sha256(payload.encode()).hexdigest())

def map_and_price(takeoff_rows, normalized_rows):
    from core.estimate.pricebook_ingestion_v1 import price_takeoff
    from core.estimate.pricebook_mapping_v2 import map_items, mapping_gate
    candidates=[{"item_code":r.item_code,"description":r.description,"unit":r.unit} for r in normalized_rows if r.unit_price is not None]
    mapped=map_items(takeoff_rows,candidates)
    gate=mapping_gate(mapped)
    if not gate["green"]: raise ValueError("pricebook mapping gate is not green")
    prices=to_price_rows(normalized_rows).accepted
    return price_takeoff([{"item_code":m.item_code,"unit":next(r.unit for r in normalized_rows if r.item_code==m.item_code),"quantity":item["quantity"]} for m,item in zip(mapped,takeoff_rows)],prices)
