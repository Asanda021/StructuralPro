"""Fail-closed validation for AI-generated takeoff candidates.

AI output is advisory. A candidate is never a confirmed takeoff merely because it
passed schema validation; an explicit human confirmation flag is required.
"""
from __future__ import annotations

import math
import re
from typing import Any


def validate_ai_takeoff_proposal(
    proposal: dict[str, Any],
    *,
    user_confirmed: bool = False,
    minimum_confidence: float = 0.85,
) -> dict[str, Any]:
    issues: list[str] = []
    if not isinstance(proposal, dict):
        return {"valid": False, "approved": False, "issues": ["پیشنهاد هوش مصنوعی باید ساختار معتبر داشته باشد"], "rows": []}
    try:
        threshold = float(minimum_confidence) if not isinstance(minimum_confidence, bool) else float("nan")
    except (TypeError, ValueError, OverflowError):
        threshold = float("nan")
    if not math.isfinite(threshold) or not 0.0 < threshold <= 1.0:
        issues.append("حد اطمینان باید عددی بین صفر و یک باشد")
    drawing_id = str(proposal.get("drawing_id", "")).strip()
    revision_id = str(proposal.get("revision_id", "")).strip()
    if not drawing_id:
        issues.append("شناسه منبع نقشه الزامی است")
    if not revision_id:
        issues.append("شناسه نسخه نقشه الزامی است")
    candidates = proposal.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        issues.append("پیشنهاد باید دست‌کم یک نامزد متره داشته باشد")
        candidates = []
    seen: set[str] = set()
    seen_session_items: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, 1):
        prefix = f"نامزد {index}"
        if not isinstance(candidate, dict):
            issues.append(f"{prefix}: ساختار نامعتبر است")
            continue
        source_id = str(candidate.get("source_id", "")).strip()
        session_item_id = str(candidate.get("session_item_id", "")).strip()
        if not source_id:
            issues.append(f"{prefix}: شناسه منبع پایدار الزامی است")
        elif source_id in seen:
            issues.append(f"{prefix}: شناسه منبع تکراری است")
        if source_id:
            seen.add(source_id)
            # List-order placeholders are not stable identities across CAD
            # revisions and must never be promoted to a priced takeoff.
            if re.fullmatch(r"entity-\d+", source_id, flags=re.IGNORECASE):
                issues.append(f"{prefix}: شناسه منبع ترتیبی و ناپایدار است")
        if not session_item_id:
            issues.append(f"{prefix}: شناسه متره هندسی ذخیره‌شده الزامی است")
        elif session_item_id in seen_session_items:
            issues.append(f"{prefix}: شناسه متره هندسی تکراری است")
        else:
            seen_session_items.add(session_item_id)
        page = candidate.get("page")
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            issues.append(f"{prefix}: شماره صفحه معتبر الزامی است")
        kind = str(candidate.get("kind", "")).strip().lower()
        expected_unit = {"length": "m", "area": "m2", "count": "عدد"}.get(kind)
        unit = str(candidate.get("unit", "")).strip()
        if expected_unit is None:
            issues.append(f"{prefix}: نوع متره پشتیبانی نمی‌شود")
        elif unit != expected_unit:
            issues.append(f"{prefix}: واحد با نوع متره سازگار نیست")
        try:
            raw_quantity = candidate.get("quantity")
            quantity = float(raw_quantity) if not isinstance(raw_quantity, bool) else float("nan")
        except (TypeError, ValueError, OverflowError):
            quantity = float("nan")
        if not math.isfinite(quantity) or quantity <= 0:
            issues.append(f"{prefix}: مقدار باید مثبت و متناهی باشد")
        if kind == "count" and math.isfinite(quantity) and not quantity.is_integer():
            issues.append(f"{prefix}: تعداد باید عدد صحیح باشد")
        try:
            raw_confidence = candidate.get("confidence")
            confidence = float(raw_confidence) if not isinstance(raw_confidence, bool) else float("nan")
        except (TypeError, ValueError, OverflowError):
            confidence = float("nan")
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            issues.append(f"{prefix}: سطح اطمینان نامعتبر است")
        elif math.isfinite(threshold) and confidence < threshold:
            issues.append(f"{prefix}: سطح اطمینان از حد مجاز کمتر است")
        evidence = candidate.get("evidence")
        if not isinstance(evidence, dict):
            issues.append(f"{prefix}: شواهد نقشه باید ساختارمند باشد")
            evidence = {}
        if str(evidence.get("source_ref", "")).strip() == "":
            issues.append(f"{prefix}: مرجع دقیق صفحه/ناحیه شواهد الزامی است")
        if kind in {"length", "area"}:
            scale_ref = str(evidence.get("scale_ref", "")).strip()
            if not scale_ref:
                issues.append(f"{prefix}: مرجع کالیبراسیون/مقیاس الزامی است")
            try:
                raw_scale = evidence.get("meters_per_pixel")
                meters_per_pixel = float(raw_scale) if not isinstance(raw_scale, bool) else float("nan")
            except (TypeError, ValueError, OverflowError):
                meters_per_pixel = float("nan")
            if not math.isfinite(meters_per_pixel) or meters_per_pixel <= 0:
                issues.append(f"{prefix}: ضریب مقیاس معتبر و مثبت الزامی است")
        formula = str(candidate.get("formula", "")).strip()
        if not formula:
            issues.append(f"{prefix}: فرمول یا روش محاسبه ثبت نشده است")
        if not str(candidate.get("label", "")).strip():
            issues.append(f"{prefix}: شرح قابل بازبینی الزامی است")
        normalized.append({
            "source_id": source_id, "session_item_id": session_item_id,
            "page": page, "kind": kind, "unit": unit,
            "quantity": quantity, "confidence": confidence,
            "evidence": evidence, "formula": formula,
            "label": str(candidate.get("label", "")).strip(),
        })
    valid = not issues
    approved = valid and user_confirmed is True
    if valid and not approved:
        issues.append("پیشنهاد معتبر است اما تا تأیید صریح کاربر، متره قطعی نیست")
    return {
        "valid": valid,
        "approved": approved,
        "requires_human_confirmation": not approved,
        "drawing_id": drawing_id,
        "revision_id": revision_id,
        "issues": issues,
        "rows": normalized if approved else [],
    }
