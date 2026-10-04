"""P77 — evidence-first pricebook row extraction.

Raw official files are never replaced by fabricated rows. This module accepts
downloaded XLS/XLSX/CSV/JSON artifacts, normalizes rows, and records provenance.
"""
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import csv, json

@dataclass(frozen=True)
class NormalizedPriceRow:
    year:int
    discipline:str
    item_code:str
    description:str
    unit:str
    unit_price:float|None
    source_sha256:str
    source_file:str

def _text(v):
    return "" if v is None else str(v).strip()

def _price(v):
    s=_text(v).replace(",","").replace("٬","")
    if not s: return None
    try: return float(s)
    except ValueError: return None

def extract_csv(path, year, discipline):
    p=Path(path); digest=sha256(p.read_bytes()).hexdigest(); rows=[]
    with p.open("r",encoding="utf-8-sig",newline="") as fh:
        for r in csv.DictReader(fh):
            code=_text(r.get("item_code") or r.get("code") or r.get("ردیف"))
            desc=_text(r.get("description") or r.get("شرح"))
            unit=_text(r.get("unit") or r.get("واحد"))
            price=_price(r.get("unit_price") or r.get("price") or r.get("بهای واحد"))
            if code or desc:
                rows.append(NormalizedPriceRow(year,discipline,code,desc,unit,price,digest,p.name))
    return rows

def extract_json(path, year, discipline):
    p=Path(path); digest=sha256(p.read_bytes()).hexdigest()
    data=json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data,dict): data=data.get("rows",[])
    out=[]
    for r in data:
        code=_text(r.get("item_code") or r.get("code") or r.get("ردیف"))
        desc=_text(r.get("description") or r.get("شرح"))
        unit=_text(r.get("unit") or r.get("واحد"))
        price=_price(r.get("unit_price") or r.get("price") or r.get("بهای واحد"))
        if code or desc: out.append(NormalizedPriceRow(year,discipline,code,desc,unit,price,digest,p.name))
    return out

def validate_rows(rows):
    if not rows: raise ValueError("no pricebook rows extracted")
    if any(not r.item_code and not r.description for r in rows):
        raise ValueError("row without code and description")
    return {"rows":len(rows),"priced_rows":sum(r.unit_price is not None for r in rows),
            "unpriced_rows":sum(r.unit_price is None for r in rows),
            "source_hashes":sorted({r.source_sha256 for r in rows})}
