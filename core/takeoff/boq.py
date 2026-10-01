"""Professional deterministic BOQ builder.

Keeps takeoff provenance, stable item coding and commercial metadata intact while
remaining backward compatible with the existing BOQ/estimate pipeline.
"""
from __future__ import annotations
from typing import Iterable, Any
import math
from .units import normalize_unit

BOQ_DEFAULT_STATUS = "active"

def _read(r: Any, name: str, default=None):
    return r.get(name, default) if isinstance(r, dict) else getattr(r, name, default)

def _text(value) -> str:
    return str(value or "").strip()

def _number(value, field: str, *, allow_none: bool = True):
    if value is None and allow_none:
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number

def build_boq(rows: Iterable[Any], aggregate: bool = True, factor: float = 1.0) -> list[dict[str, Any]]:
    factor = _number(factor, "factor", allow_none=False)
    if factor < 0:
        raise ValueError("factor must be finite and non-negative")
    raw = []
    for r in rows:
        source = _text(_read(r, "source", ""))
        source_id = _text(_read(r, "source_id", ""))
        source_type = _text(_read(r, "source_type", "manual")) or "manual"
        q = _number(_read(r, "quantity", 0), "quantity", allow_none=False)
        if q < 0:
            raise ValueError("quantity must be finite and non-negative")
        raw_unit = _text(_read(r, "unit", ""))
        if not raw_unit:
            raise ValueError("unit is required")
        unit = normalize_unit(raw_unit)
        price = _number(_read(r, "unit_price", None), "unit_price")
        if price is not None and price < 0:
            raise ValueError("unit_price must be finite and non-negative")
        code = _text(_read(r, "price_code", "")) or None
        item_code = _text(_read(r, "item_code", "")) or code
        description = _text(_read(r, "description", ""))
        if not description:
            raise ValueError("description is required")
        chapter = _text(_read(r, "chapter", ""))
        category = _text(_read(r, "category", "")) or chapter
        group = _text(_read(r, "group", "")) or category or "سایر"
        f = _number(_read(r, "factor", factor), "factor", allow_none=False)
        if f < 0:
            raise ValueError("factor must be finite and non-negative")
        status = _text(_read(r, "status", BOQ_DEFAULT_STATUS)) or BOQ_DEFAULT_STATUS
        notes = _text(_read(r, "notes", ""))
        total = None if price is None else round(q * price * f, 10)
        warning = ""
        if price == 0:
            warning = "zero_price"
        raw.append({
            "source": source, "source_id": source_id, "source_ids": [source_id] if source_id else [], "source_type": source_type,
            "item_code": item_code, "price_code": code, "chapter": chapter,
            "category": category, "group": group, "description": description,
            "quantity": q, "unit": unit, "unit_price": price, "total": total,
            "factor": f, "status": status, "notes": notes, "warning": warning,
        })
    if aggregate:
        groups = {}
        for r in raw:
            key = (
                r["item_code"] or r["price_code"] or r["description"], r["unit"],
                r["unit_price"], r["factor"], r["chapter"], r["category"],
                r["group"], r["status"],
            )
            if key not in groups:
                groups[key] = dict(r)
            else:
                groups[key]["quantity"] += r["quantity"]
                for source_id in r.get("source_ids", []):
                    if source_id and source_id not in groups[key]["source_ids"]:
                        groups[key]["source_ids"].append(source_id)
                if r["total"] is not None:
                    groups[key]["total"] = round((groups[key]["total"] or 0) + r["total"], 10)
        raw = list(groups.values())
    return [dict(item_no=i, **r) for i, r in enumerate(raw, 1)]

def validate_boq_structure(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    errors, warnings, codes = [], [], set()
    for index, row in enumerate(rows, 1):
        code = _text(row.get("price_code") or row.get("item_code"))
        if not code:
            warnings.append({"item_no": index, "code": "missing_item_code"})
        elif code in codes:
            warnings.append({"item_no": index, "code": "duplicate_item_code", "value": code})
        codes.add(code)
        if not _text(row.get("description")):
            errors.append({"item_no": index, "code": "missing_description"})
        if not _text(row.get("unit")):
            errors.append({"item_no": index, "code": "missing_unit"})
        if _text(row.get("status")) not in {"active", "cancelled", "draft"}:
            warnings.append({"item_no": index, "code": "unknown_status", "value": row.get("status")})
        try:
            q = float(row.get("quantity", 0))
            if not math.isfinite(q) or q < 0:
                errors.append({"item_no": index, "code": "invalid_quantity"})
        except (TypeError, ValueError):
            errors.append({"item_no": index, "code": "invalid_quantity"})
    return {"valid": not errors, "errors": errors, "warnings": warnings, "line_count": len(rows)}

def boq_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    return {
        "line_count": len(rows),
        "active_line_count": sum(1 for r in rows if r.get("status", "active") == "active"),
        "quantity_by_unit": _sum_by(rows, "unit", "quantity"),
        "amount_by_code": _sum_by(rows, "price_code", "total"),
        "amount_by_group": _sum_by(rows, "group", "total"),
        "grand_total": sum(float(r.get("total") or 0) for r in rows),
        "warnings": [r for r in rows if r.get("warning")],
    }

def _sum_by(rows, key, value):
    out = {}
    for r in rows:
        k = r.get(key) or "بدون کد"
        out[k] = out.get(k, 0) + float(r.get(value) or 0)
    return out
