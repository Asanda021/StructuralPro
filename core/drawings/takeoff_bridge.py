"""Fail-closed adapter from DrawingTakeoffSession to reviewable takeoff rows.

This adapter does not write to project storage. The application must persist the
returned rows through its owning project service to preserve BOQ/estimate links,
revisions, and audit events.
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
    takeoff_code: str = ""
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
            "takeoff_code": self.takeoff_code,
            "status": self.status,
        }


_KIND_UNITS = {"length": "m", "area": "m2", "count": "عدد"}


def prepare_drawing_takeoff_rows(items: Iterable[Any], *, drawing_source: str) -> tuple[DrawingTakeoffRow, ...]:
    """Validate session measurements without inventing values or BOQ codes."""
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
        if not item_id or not source_ref:
            raise ValueError("هر ردیف نقشه باید شناسه و ارجاع منبع داشته باشد")
        identity = item_source or source_ref
        if identity in seen:
            raise ValueError(f"منبع متره تکراری و مستعد دوباره‌شماری: {identity}")
        seen.add(identity)
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
        # Session-generated refs include the source plus page and item identity.
        expected_prefix = f"{source}#page={page}&takeoff={item_id}"
        if source_ref != expected_prefix and not source_ref.startswith(expected_prefix + "&"):
            raise ValueError("ارجاع ردیف با شناسه نقشه/صفحه/متره همخوانی ندارد")
        label = str(get("label", "") or "").strip()
        takeoff_code = str(get("takeoff_code", "") or "").strip()
        rows.append(DrawingTakeoffRow(
            source_id=f"drawing:{source}:page:{page}:{item_id}",
            source_ref=source_ref,
            page=page,
            kind=kind,
            quantity=quantity,
            unit=_KIND_UNITS[kind],
            description=label or f"متره {kind} از نقشه — نیازمند بازبینی کاربر",
            formula=formula,
            takeoff_code=takeoff_code,
        ))
    return tuple(rows)


def prepare_session_takeoff(session: Any) -> tuple[DrawingTakeoffRow, ...]:
    """Adapt an actual DrawingTakeoffSession while enforcing per-page calibration."""
    source = str(getattr(session, "drawing_source", "") or "").strip()
    if not source:
        raise ValueError("جلسه متره به نقشه منبع متصل نیست")
    items = tuple(getattr(session, "items", ()))
    calibrations = getattr(session, "calibrations", {})
    for item in items:
        if str(getattr(item, "kind", "")).casefold() in {"length", "area"}:
            if int(getattr(item, "page", 0)) not in calibrations:
                raise ValueError(f"کالیبراسیون صریح صفحه {getattr(item, 'page', '?')} یافت نشد")
    return prepare_drawing_takeoff_rows(items, drawing_source=source)


def build_takeoff_export_payload(session: Any) -> dict[str, Any]:
    """Build a versioned JSON interchange payload for the application's BOQ import path."""
    rows = prepare_session_takeoff(session)
    return {
        "schema": "structuralpro.drawing-takeoff.v1",
        "drawing_source": str(session.drawing_source),
        "approval_required": True,
        "items": [row.to_dict() for row in rows],
        "summary": {
            "items": len(rows),
            "needs_review": len(rows),
            "by_unit": {
                unit: sum(row.quantity for row in rows if row.unit == unit)
                for unit in sorted({row.unit for row in rows})
            },
        },
    }
