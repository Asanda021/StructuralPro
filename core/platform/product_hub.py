"""Product-level orchestration for StructuralPro's benchmark capabilities.

The hub is deliberately UI-agnostic. Windows, Android and Telegram clients can
use the same capability names, action contracts, project lifecycle, drawing/
estimate bridges and validation rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy
from typing import Any, Callable, Iterable, Mapping

from .parity import capability_matrix


@dataclass(frozen=True)
class FeatureAction:
    capability_id: str
    action: str
    description: str
    kind: str = "core"
    handler: Callable[..., Any] | None = field(default=None, compare=False, repr=False)

    def run(self, *args, **kwargs):
        if self.handler is None:
            raise NotImplementedError(
                f"برای قابلیت {self.capability_id} هنوز آداپتور اجرایی متصل نشده است."
            )
        return self.handler(*args, **kwargs)


class ProductHub:
    """Single application service shared by all StructuralPro clients."""

    def __init__(self, project_service=None, pricing=None, sync=None):
        self.project_service = project_service
        self.pricing = pricing
        self.sync = sync
        self._actions: dict[str, FeatureAction] = {}
        self._register_contracts()

    def _register(self, capability_id: str, action: str, description: str,
                  handler: Callable[..., Any] | None = None, kind: str = "core"):
        self._actions[capability_id] = FeatureAction(
            capability_id, action, description, kind, handler
        )

    def _register_contracts(self):
        """Register all benchmark capabilities in one stable API surface."""
        descriptions = {
            "cad-dwg": "ورود DWG از طریق آداپتور تبدیل/خواندن",
            "cad-dxf": "ورود DXF",
            "cad-layers": "استخراج لایه‌ها",
            "cad-lines": "استخراج خط",
            "cad-polylines": "استخراج پلی‌لاین",
            "cad-arcs": "استخراج قوس",
            "cad-circles": "استخراج دایره",
            "cad-ellipse": "استخراج بیضی",
            "cad-blocks": "استخراج و شمارش بلاک",
            "cad-text": "استخراج متن",
            "cad-hatch": "استخراج Hatch",
            "cad-dimensions": "استخراج Dimension",
            "cad-xref": "ردیابی Xref",
            "cad-units": "یکسان‌سازی واحد نقشه",
            "cad-scale": "کالیبراسیون مقیاس",
            "cad-viewport": "مدیریت چند Viewport",
            "takeoff-length": "متره طولی",
            "takeoff-area": "متره مساحتی",
            "takeoff-count": "متره تعدادی",
            "takeoff-volume": "متره حجمی",
            "takeoff-perimeter": "متره محیطی",
            "takeoff-depth": "متره عمق‌محور",
            "takeoff-cutout": "کسر بازشو و Cutout",
            "takeoff-formula": "فرمول سفارشی مقدار",
            "takeoff-waste": "ضریب پرت",
            "takeoff-classification": "طبقه‌بندی سفارشی",
            "takeoff-markup": "ذخیره متادیتای Markup",
            "takeoff-legend": "Legend متره",
            "takeoff-visual-search": "جست‌وجوی نماد",
            "takeoff-dynamic-fill": "Dynamic Fill",
            "takeoff-ai-count": "شمارش AI محلی",
            "takeoff-ai-map": "Map هوشمند",
            "revision-drawing": "مقایسه نسخه نقشه",
            "revision-overlay": "Overlay نسخه‌ها",
            "revision-history": "تاریخچه نسخه",
            "revision-quantity-delta": "اختلاف مقدار بین نسخه‌ها",
            "bim-ifc": "ورود IFC",
            "bim-objects": "طبقه‌بندی آبجکت BIM",
            "bim-quantities": "استخراج مقادیر BIM",
            "bim-2d3d-link": "پیوند متره 2D/3D",
            "project-templates": "قالب پروژه",
            "project-library": "کتابخانه پروژه",
            "project-package": "بسته پروژه",
            "project-backup": "پشتیبان پروژه",
            "project-audit": "ردپای تغییرات",
            "project-health": "کنترل آمادگی پروژه",
            "collab-members": "اعضای پروژه",
            "collab-roles": "سطوح دسترسی",
            "collab-comments": "نظر و تأیید",
            "collab-realtime": "قرارداد همکاری آنلاین",
            "cloud-sync": "همگام‌سازی ابری",
            "cloud-offline": "صف همگام‌سازی آفلاین",
            "pricing-years": "فهرست‌بهای سالانه",
            "pricing-search": "جست‌وجوی کد/شرح",
            "pricing-import": "ورود فهرست‌بها",
            "pricing-export": "خروجی فهرست‌بها",
            "pricing-analysis": "تجزیه‌بها",
            "pricing-resources": "کتابخانه منابع",
            "pricing-snapshot": "Snapshot قیمت",
            "pricing-indexation": "تعدیل/شاخص",
            "pricing-real-data": "آماده‌سازی برای داده رسمی سالانه",
            "estimate-boq": "ساخت BOQ",
            "estimate-assemblies": "برآورد اسمبلی‌محور",
            "estimate-factors": "ضرایب پیمان",
            "estimate-transport": "هزینه حمل",
            "estimate-cost-breakdown": "ریز هزینه",
            "estimate-history": "نسخه‌های برآورد",
            "estimate-change": "ردیابی تغییر برآورد",
            "statement-multi": "صورت‌وضعیت دوره‌ای",
            "statement-cumulative": "تجمع مقادیر",
            "statement-retention": "کسورات/سپرده",
            "statement-finalize": "نهایی‌سازی",
            "statement-financial": "خلاصه مالی",
            "reports-pdf": "گزارش PDF",
            "reports-excel": "گزارش Excel",
            "reports-word": "گزارش Word",
            "reports-csv": "گزارش CSV",
            "reports-custom": "سازنده گزارش سفارشی",
            "integration-excel": "قرارداد لینک Excel",
            "integration-api": "قرارداد API",
            "integration-transfer": "انتقال پروژه/عضو",
            "integration-cad": "پل CAD به BOQ",
            "ai-missing": "تشخیص ورودی ناقص",
            "ai-next": "پیشنهاد گام بعدی",
            "ai-assistant": "دستیار متنی محلی",
            "ai-qa": "کنترل کیفیت AI",
            "security-license": "مجوز و حساب",
            "platform-windows": "کلاینت Windows",
            "platform-android": "قرارداد کلاینت Android",
            "platform-telegram": "قرارداد کلاینت Telegram",
            "ux-rtl": "رابط RTL",
            "ux-shortcuts": "میانبرهای صفحه‌کلید",
            "ux-presets": "ورودی‌های آماده",
            "domain-structural": "دامنه سازه",
            "domain-architectural": "دامنه معماری",
            "domain-mechanical": "دامنه مکانیک",
            "domain-electrical": "دامنه برق",
            "domain-civil": "دامنه عمرانی",
            "domain-mep-coordination": "هماهنگی MEP",
            "document-links": "پیوند سند و نقشه",
        }
        for cap in capability_matrix():
            self._register(
                cap["id"], cap["id"],
                descriptions.get(cap["id"], cap["title"]),
                kind=cap["category"],
            )

    def capabilities(self) -> list[dict[str, Any]]:
        return [
            {
                "id": a.capability_id,
                "action": a.action,
                "description": a.description,
                "kind": a.kind,
                "has_handler": a.handler is not None,
            }
            for a in self._actions.values()
        ]

    def get(self, capability_id: str) -> FeatureAction:
        try:
            return self._actions[capability_id]
        except KeyError as exc:
            raise KeyError(f"قابلیت ناشناخته: {capability_id}") from exc

    def set_handler(self, capability_id: str, handler: Callable[..., Any]):
        old = self.get(capability_id)
        self._actions[capability_id] = FeatureAction(
            old.capability_id, old.action, old.description, old.kind, handler
        )

    def validate_project(self, project: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Deterministic project QA used before estimate/export/sync."""
        issues: list[dict[str, Any]] = []
        if not str(project.get("name", "")).strip():
            issues.append({
                "code": "missing_project_name",
                "severity": "error",
                "message": "نام پروژه وارد نشده است.",
            })
        for i, takeoff in enumerate(project.get("takeoffs", []) or []):
            member = takeoff.get("member_code") or f"ردیف {i + 1}"
            for q in takeoff.get("quantities", []) or []:
                try:
                    value = float(q.get("amount"))
                except (TypeError, ValueError):
                    issues.append({
                        "code": "invalid_quantity",
                        "severity": "error",
                        "member": member,
                        "message": f"مقدار {q.get('title', q.get('code', ''))} معتبر نیست.",
                    })
                    continue
                if value < 0:
                    issues.append({
                        "code": "negative_quantity",
                        "severity": "error",
                        "member": member,
                        "message": "مقدار منفی مجاز نیست.",
                    })
                if not q.get("unit"):
                    issues.append({
                        "code": "missing_unit",
                        "severity": "warning",
                        "member": member,
                        "message": "واحد مقدار مشخص نشده است.",
                    })
        return issues

    def apply_bulk(
        self,
        project: Mapping[str, Any],
        changes: Mapping[str, Any],
        member_codes: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Apply one set of fields to multiple members without repeated entry."""
        result = deepcopy(dict(project))
        wanted = set(member_codes or [])
        for takeoff in result.get("takeoffs", []) or []:
            if wanted and takeoff.get("member_code") not in wanted:
                continue
            takeoff.update(deepcopy(dict(changes)))
        result["updated_at"] = datetime.now().isoformat(timespec="seconds")
        return result

    def duplicate_takeoff(
        self, project: Mapping[str, Any], member_code: str, copies: int = 1
    ) -> dict[str, Any]:
        """Clone a takeoff row for repetitive members."""
        result = deepcopy(dict(project))
        rows = result.setdefault("takeoffs", [])
        source = next(
            (x for x in rows if x.get("member_code") == member_code), None
        )
        if source is None:
            raise KeyError(f"عضو {member_code} پیدا نشد.")
        import uuid
        for _ in range(max(0, int(copies))):
            clone = deepcopy(source)
            clone["id"] = uuid.uuid4().hex
            clone["member_code"] = f"{member_code}-{len(rows) + 1}"
            rows.append(clone)
        result["updated_at"] = datetime.now().isoformat(timespec="seconds")
        return result

    def summary(self) -> dict[str, Any]:
        matrix = capability_matrix()
        return {
            "total_capabilities": len(matrix),
            "catalog_version": "1.0",
            "clients": ["windows", "android-contract", "telegram-contract"],
            "offline_core": True,
            "local_ai": True,
            "cloud_optional": True,
            "registered": len(self._actions),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }
