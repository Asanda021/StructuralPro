"""Professional estimate orchestration with explicit finalization gates."""
from __future__ import annotations
from typing import Iterable,Any
import math
from core.takeoff.boq import build_boq,validate_boq_structure,boq_summary
from core.takeoff.costing import cost_breakdown
def _num(value,name):
    x=float(value)
    if not math.isfinite(x) or x<0: raise ValueError(f"{name} must be finite and non-negative")
    return x
def _validate_factors(factors):
    out={}
    for name,value in (factors or {}).items():
        key=str(name).strip()
        if not key: raise ValueError("factor name cannot be empty")
        out[key]=_num(value,"factor rate")
    return out
def build_estimate(rows:Iterable[Any],*,factors=None,aggregate=True)->dict[str,Any]:
    normalized=_validate_factors(factors); boq=build_boq(rows,aggregate=aggregate); validation=validate_boq_structure(boq)
    cost=cost_breakdown(boq,normalized)
    unpriced = [row["item_no"] for row in boq
                if row.get("status", "active") == "active" and row.get("unit_price") is None]
    return {"boq":boq,"summary":boq_summary(boq),"validation":validation,"cost":cost,"factors":normalized,
            "unpriced_item_numbers": unpriced, "finalizable":bool(validation["valid"] and not unpriced)}

def compare_estimates(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Compare all BOQ lines without collapsing equal price codes.

    Same-code rows must have distinct, stable source identities. Missing prices
    remain None; they are never misreported as an explicit zero price.
    """
    a = _num(old.get("cost", {}).get("grand_total", 0), "old estimate total")
    b = _num(new.get("cost", {}).get("grand_total", 0), "new estimate total")
    old_list = list(old.get("boq", []) or [])
    new_list = list(new.get("boq", []) or [])

    def base_key(row: dict[str, Any], index: int) -> str:
        return str(row.get("price_code") or row.get("item_code") or
                   row.get("description") or row.get("source") or index).strip()

    def stable_source(row: dict[str, Any]) -> str:
        ids = row.get("source_ids") or []
        source = row.get("source_id") or (ids[0] if len(ids) == 1 else None)
        return str(source or row.get("source") or "").strip()

    def duplicate_bases(items: list[dict[str, Any]]) -> set[str]:
        seen: set[str] = set()
        duplicate: set[str] = set()
        for i, row in enumerate(items):
            key = base_key(row, i)
            if key in seen:
                duplicate.add(key)
            seen.add(key)
        return duplicate

    ambiguous = duplicate_bases(old_list) | duplicate_bases(new_list)

    def index_rows(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for i, row in enumerate(items):
            key = base_key(row, i)
            if key in ambiguous:
                source = stable_source(row)
                if not source:
                    raise ValueError(f"ambiguous BOQ comparison identity for code {key}")
                key = f"{key}|source:{source}"
            if key in indexed:
                raise ValueError(f"duplicate BOQ comparison identity: {key}")
            indexed[key] = row
        return indexed

    old_rows = index_rows(old_list)
    new_rows = index_rows(new_list)
    line_changes = []

    def quantity(row: dict[str, Any] | None) -> float:
        return _num(row["quantity"], "comparison quantity") if row is not None else 0.0

    def price(row: dict[str, Any] | None) -> float | None:
        if row is None or row.get("unit_price") is None:
            return None
        return _num(row["unit_price"], "comparison unit price")

    for key in sorted(old_rows.keys() | new_rows.keys()):
        before, after = old_rows.get(key), new_rows.get(key)
        bq, aq = quantity(before), quantity(after)
        bp, ap = price(before), price(after)
        if bq != aq or bp != ap:
            line_changes.append({
                "key": key, "old_quantity": bq, "new_quantity": aq,
                "quantity_delta": aq - bq,
                "old_unit_price": bp, "new_unit_price": ap,
                "unit_price_delta": ap - bp if bp is not None and ap is not None else None,
            })
    return {
        "old_total": a, "new_total": b, "delta": b - a,
        "delta_percent": 0.0 if a == 0 else (b - a) / a * 100,
        "line_changes": line_changes,
        "added_lines": sorted(new_rows.keys() - old_rows.keys()),
        "removed_lines": sorted(old_rows.keys() - new_rows.keys()),
    }
