"""Fail-closed validation for AI-proposed takeoff results.

AI output is a proposal, never an authoritative measurement. This guard requires
explicit user confirmation, drawing provenance, explicit scale for geometry-based
results, supported units, and finite non-negative quantities before a proposal can
be passed to a review/persistence workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping


@dataclass(frozen=True)
class GuardedTakeoffProposal:
    quantity: float
    unit: str
    source_ref: str
    scale_ref: str | None
    method: str
    description: str
    user_confirmed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "quantity": self.quantity,
            "unit": self.unit,
            "source_ref": self.source_ref,
            "scale_ref": self.scale_ref,
            "method": self.method,
            "description": self.description,
            "user_confirmed": self.user_confirmed,
            "status": "user_confirmed_proposal",
        }


_ALLOWED_UNITS = {"m", "m2", "m3", "kg", "t", "عدد", "set", "l", "hr"}
_GEOMETRY_METHODS = {"pixel_geometry", "drawing_geometry", "image_geometry", "cad_geometry"}


def validate_ai_takeoff_proposal(payload: Mapping[str, Any], *, user_confirmed: bool = False) -> GuardedTakeoffProposal:
    """Validate, but never silently repair or complete, an AI takeoff proposal."""
    if not isinstance(payload, Mapping):
        raise ValueError("خروجی هوش مصنوعی باید ساختار داده معتبر داشته باشد")
    if not user_confirmed:
        raise ValueError("خروجی هوش مصنوعی تا پیش از تأیید صریح کاربر قابل ثبت نیست")
    try:
        quantity = float(payload.get("quantity"))
    except (TypeError, ValueError):
        raise ValueError("مقدار پیشنهادی باید عددی و صریح باشد")
    if not math.isfinite(quantity) or quantity < 0:
        raise ValueError("مقدار پیشنهادی باید متناهی و نامنفی باشد")
    unit = str(payload.get("unit", "") or "").strip().casefold()
    if unit not in _ALLOWED_UNITS:
        raise ValueError("واحد خروجی نامشخص یا پشتیبانی‌نشده است؛ واحد حدس زده نمی‌شود")
    source_ref = str(payload.get("source_ref", "") or "").strip()
    if not source_ref:
        raise ValueError("ارجاع به نقشه/سند منبع برای ثبت خروجی الزامی است")
    method = str(payload.get("method", "") or "").strip().casefold()
    if not method:
        raise ValueError("روش استخراج مقدار باید مشخص باشد")
    scale_ref = str(payload.get("scale_ref", "") or "").strip() or None
    if method in _GEOMETRY_METHODS and not scale_ref:
        raise ValueError("برای مقدار هندسی استخراج‌شده از نقشه، ارجاع کالیبراسیون صریح لازم است")
    description = str(payload.get("description", "") or "").strip()
    if not description:
        raise ValueError("شرح آیتم باید صریح باشد؛ شرح خودکار حدس زده نمی‌شود")
    return GuardedTakeoffProposal(
        quantity=quantity,
        unit=unit,
        source_ref=source_ref,
        scale_ref=scale_ref,
        method=method,
        description=description,
        user_confirmed=True,
    )
