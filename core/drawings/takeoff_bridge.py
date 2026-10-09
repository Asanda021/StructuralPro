"""Fail-closed adapter from calibrated drawing measurements to reviewable takeoff rows.

This module deliberately does not write to project storage. Callers must show the
prepared rows to a user and persist them through the application's normal service,
so source references and project-specific BOQ links remain under the owning service.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class DrawingTakeoffRow:
    source_id: str
    source_ref: str
    page: int
    kind: str
    quantity: float
    unit: str
    description: str
    formula: str
    status: str = "needs_review"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_ref": self.source_ref,
            "page": self.page,
            "kind": self.kind,
            "quantity": self.quantity,
            "unit": self.unit,
            "description": self.description,
            "formula": self.formula,
            "status": self.status,
        }


_KIND_UNITS = {"length": "m", "area": "m2", "count": "عدد"}


def prepare_drawing_takeoff_rows(items: Iterable[Any], *, drawing_source: str) -> tuple[DrawingTakeoffRow, ...]:
    """Validate drawing measurements and map them to reviewable, traceable rows.

    Does not infer missing scale, quantity, unit, drawing identity, or BOQ code.
    Each item must have been calculated by the drawing session after any required
    explicit page calibration. Duplicate source identities are rejected.
    """
    source = str(drawing_source or "").strip()
    if not source:
        raise ValueError("شناسه/مسیر نقشه برای ردیابی متره الزامی است")
    rows: list[DrawingTakeoffRow] = []
    seen: set[str] = set()
    for item in items:
        get = item.get if isinstance(item, Mapping) else lambda key, default=None: getattr(item, key, default)
        item_id = str(get("id", "") or "").strip()
        item_source = str(get("source", "") or "").strip()
        source_ref = str(get("source_ref", "") or "").strip()
        kind = str(get("kind", "") or "").strip().casefold()
        if not item_id or not item_source or not source_ref:
            raise ValueError("هر ردیف نقشه باید شناسه، منبع و ارجاع منبع داشته باشد")
        if item_source in seen:
            raise ValueError(f"منبع متره تکراری و مستعد دوباره‌شماری: {item_source}")
        seen.add(item_source)
        if kind not in _KIND_UNITS:
            raise ValueError(f"نوع متره نقشه پشتیبانی نمی‌شود: {kind or 'نامشخص'}")
        try:
            quantity = float(get("quantity", get("value", None)))
            page = int(get("page", 0))
        except (TypeError, ValueError):
            raise ValueError("مقدار و شماره صفحه متره باید معتبر باشند")
        if not math.isfinite(quantity) or quantity <= 0:
            raise ValueError("مقدار متره باید مثبت و متناهی باشد")
        if page < 1:
            raise ValueError("شماره صفحه نقشه باید مثبت باشد")
        formula = str(get("formula", "") or "").strip()
        if not formula:
            raise ValueError("فرمول/مبنای محاسبه برای ردیابی متره الزامی است")
        label = str(get("label", "") or "").strip()
        rows.append(DrawingTakeoffRow(
            source_id=f"drawing:{source}:page:{page}:{item_id}",
            source_ref=source_ref,
            page=page,
            kind=kind,
            quantity=quantity,
            unit=_KIND_UNITS[kind],
            description=label or f"متره {kind} از نقشه — نیازمند بازبینی کاربر",
            formula=formula,
        ))
    return tuple(rows)
