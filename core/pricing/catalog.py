"""Offline-first price catalog with year/discipline/chapter indexing and snapshots."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, Any
import csv
from io import StringIO

@dataclass(frozen=True)
class PriceItem:
    year: int
    group: str
    chapter: str
    code: str
    description: str
    unit: str
    unit_price: float
    analysis: str = ""
    notes: str = ""

class PriceCatalog:
    def __init__(self, items: Iterable[PriceItem] = ()):
        self._items: dict[tuple[int,str], PriceItem] = {}
        self.replace(items)

    def replace(self, items: Iterable[PriceItem]) -> None:
        self._items = {(int(x.year), str(x.code).strip()): x for x in items}

    def add(self, item: PriceItem) -> None:
        key = (int(item.year), str(item.code).strip())
        if not item.code.strip():
            raise ValueError("price code is required")
        if item.unit_price < 0:
            raise ValueError("unit price cannot be negative")
        self._items[key] = item

    def years(self) -> list[int]:
        return sorted({k[0] for k in self._items}, reverse=True)

    def groups(self, year: int | None = None) -> list[str]:
        return sorted({x.group for x in self._items.values() if year is None or x.year == year})

    def chapters(self, year: int | None = None, group: str | None = None) -> list[str]:
        return sorted({x.chapter for x in self._items.values()
                       if (year is None or x.year == year) and (group is None or x.group == group)})

    def get(self, code: str, year: int | None = None) -> PriceItem | None:
        code = code.strip()
        if year is not None:
            return self._items.get((int(year), code))
        matches = [x for (y,c), x in self._items.items() if c == code]
        return sorted(matches, key=lambda x: x.year, reverse=True)[0] if matches else None

    def search(self, query: str, year: int | None = None, group: str | None = None,
               chapter: str | None = None, limit: int = 100) -> list[PriceItem]:
        q = query.strip().casefold()
        rows = []
        for x in self._items.values():
            if year is not None and x.year != int(year): continue
            if group is not None and x.group != group: continue
            if chapter is not None and x.chapter != chapter: continue
            hay = " ".join((x.code, x.description, x.unit, x.analysis, x.notes)).casefold()
            if not q or q in hay:
                rows.append(x)
        rows.sort(key=lambda x: (x.year, x.code), reverse=True)
        return rows[:max(1, limit)]

    def resolve(self, code: str, year: int | None = None, unit: str | None = None) -> dict[str, Any]:
        item = self.get(code, year)
        if item is None: return {"status":"not_found", "code":code}
        if unit and item.unit.strip() != unit.strip():
            return {"status":"unit_mismatch", "code":code, "expected_unit":item.unit, "actual_unit":unit}
        if item.unit_price < 0: return {"status":"invalid_price", "code":code}
        if item.unit_price == 0: return {"status":"zero_price", "code":code, "item":item}
        return {"status":"ok", "code":code, "item":item, "unit_price":item.unit_price}

    def snapshot(self, codes: Iterable[str], year: int | None = None) -> list[dict[str, Any]]:
        out=[]
        for code in codes:
            item=self.get(code, year)
            if item is not None:
                out.append(asdict(item))
        return out

    def export_csv(self, year: int | None = None) -> str:
        rows=[x for x in self._items.values() if year is None or x.year == int(year)]
        buf=StringIO()
        fields=["year","group","chapter","code","description","unit","unit_price","analysis","notes"]
        w=csv.DictWriter(buf, fieldnames=fields); w.writeheader()
        for x in sorted(rows,key=lambda z:(z.year,z.code)): w.writerow(asdict(x))
        return buf.getvalue()

    def import_csv(self, text: str, replace_year: bool = False) -> int:
        reader=csv.DictReader(StringIO(text))
        rows=[]
        for raw in reader:
            rows.append(PriceItem(
                year=int(raw["year"]), group=raw["group"].strip(), chapter=raw["chapter"].strip(),
                code=raw["code"].strip(), description=raw["description"].strip(), unit=raw["unit"].strip(),
                unit_price=float(raw["unit_price"]), analysis=raw.get("analysis",""), notes=raw.get("notes","")))
        if replace_year:
            years={x.year for x in rows}
            self._items={k:v for k,v in self._items.items() if k[0] not in years}
        for x in rows: self.add(x)
        return len(rows)
