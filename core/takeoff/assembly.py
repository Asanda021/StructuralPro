"""Assembly-based construction takeoff.

An assembly is a user-facing operation composed of independently auditable
components.  No component uses a hidden blanket coefficient: formulas either
derive from supplied geometry/specification or return a clear missing-input
requirement.

The model follows the Parts/Assemblies workflow used by PlanSwift while keeping
Iranian quantity-takeoff practice explicit and traceable.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Mapping


@dataclass(frozen=True)
class AssemblyComponent:
    code: str
    title: str
    unit: str
    formula: str
    quantity: float
    source: str = "derived"
    warning: str = ""


@dataclass(frozen=True)
class AssemblyResult:
    code: str
    title: str
    components: tuple[AssemblyComponent, ...]
    inputs_used: tuple[str, ...]
    missing_inputs: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.missing_inputs


def _n(p: Mapping[str, Any], name: str, minimum: float = 0.0) -> float:
    try:
        value = float(p[name])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{name} must be numeric")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _optional(p: Mapping[str, Any], name: str) -> float | None:
    if name not in p or p[name] in (None, ""):
        return None
    return _n(p, name)


def _waste(q: float, factor: float | None) -> float:
    if factor is None:
        return q
    if factor < 0:
        raise ValueError("waste_factor must be >= 0")
    return q * (1.0 + factor)


def _missing(*names: str) -> AssemblyResult:
    return AssemblyResult("", "", (), (), tuple(names))


def calculate_assembly(code: str, **p: Any) -> AssemblyResult:
    """Calculate a real assembly without inventing unspecified specifications.

    Waste is expressed as a fraction (e.g. 0.05 = 5%).  It is optional and
    never silently assumed.
    """
    k = code.strip().casefold().replace(" ", "_")

    # Block wall: geometry determines net area and nominal volume.  Block size
    # and mortar joint/mix are specification inputs, not fixed coefficients.
    if k in {"block_wall", "masonry_block_wall", "دیوار_بلوک"}:
        L, H, t = _n(p, "length"), _n(p, "height"), _n(p, "thickness")
        openings = _n({"openings": p.get("openings", 0)}, "openings")
        area = max(0.0, L * H - openings)
        volume = area * t
        bw = _optional(p, "block_length")
        bh = _optional(p, "block_height")
        bt = _optional(p, "block_thickness")
        joint = _optional(p, "joint_thickness")
        mortar_ratio_c = _optional(p, "cement_parts")
        mortar_ratio_s = _optional(p, "sand_parts")
        if None in (bw, bh, bt, joint, mortar_ratio_c, mortar_ratio_s):
            return AssemblyResult(
                "block_wall", "دیوار بلوکی", (),
                ("length", "height", "thickness", "openings"),
                tuple(x for x, v in (
                    ("block_length", bw), ("block_height", bh),
                    ("block_thickness", bt), ("joint_thickness", joint),
                    ("cement_parts", mortar_ratio_c), ("sand_parts", mortar_ratio_s),
                ) if v is None),
            )
        block_nominal = (bw + joint) * (bh + joint) * bt
        blocks = area / ((bw + joint) * (bh + joint))
        block_waste = _optional(p, "block_waste_factor")
        blocks_final = ceil(_waste(blocks, block_waste))
        # Procurement waste must not change the geometric built-wall volume.
        mortar_volume = max(0.0, volume - blocks * bw * bh * bt)
        mortar_waste = _optional(p, "mortar_waste_factor")
        mortar_final = _waste(mortar_volume, mortar_waste)
        total_parts = mortar_ratio_c + mortar_ratio_s
        cement_volume = mortar_final * mortar_ratio_c / total_parts
        sand_volume = mortar_final * mortar_ratio_s / total_parts
        return AssemblyResult(
            "block_wall", "دیوار بلوکی", (
                AssemblyComponent("wall_area", "سطح خالص دیوار", "m²", "L×H−بازشو", area),
                AssemblyComponent("block", "بلوک", "عدد", "ceil(A/((Lb+j)×(Hb+j))×(1+پرت))", float(blocks_final), warning=f"مبنای ابعاد بلوک {bw}×{bh}×{bt} m"),
                AssemblyComponent("mortar", "ملات", "m³", "Vwall−Vblock", mortar_final),
                AssemblyComponent("cement", "سیمان ملات", "m³", "Vmort×سهم سیمان", cement_volume),
                AssemblyComponent("sand", "ماسه ملات", "m³", "Vmort×سهم ماسه", sand_volume),
            ),
            ("length", "height", "thickness", "openings", "block_length", "block_height",
             "block_thickness", "joint_thickness", "cement_parts", "sand_parts"),
        )

    # Joist/foam roof: concrete is computed from actual topping and rib
    # geometry.  Foam and joist quantities come from actual module dimensions;
    # reinforcement is only calculated when its specification is supplied.
    if k in {"joist_foam_roof_assembly", "joist_block_roof_assembly", "سقف_تیرچه_یونولیت"}:
        L, W = _n(p, "length"), _n(p, "width")
        count = _n({"count": p.get("count", 1)}, "count", 1)
        area = L * W * count
        topping = _n(p, "topping_thickness")
        spacing = _n(p, "joist_spacing", 1e-12)
        jw = _n(p, "joist_width")
        jd = _n(p, "joist_depth")
        joist_count = _optional(p, "joist_count")
        if joist_count is None:
            joist_count = ceil(W / spacing) + 1
        joists = joist_count * count
        concrete = area * topping + joists * L * jw * jd
        foam_l = _optional(p, "foam_length")
        foam_w = _optional(p, "foam_width")
        foam_h = _optional(p, "foam_height")
        if None in (foam_l, foam_w, foam_h):
            return AssemblyResult(
                k, "سقف تیرچه یونولیت" if "foam" in k or "یونولیت" in k else "سقف تیرچه‌بلوک", (
                    AssemblyComponent("concrete", "بتن", "m³",
                                      "A×t رویه+تعداد تیرچه×L×b×h", concrete),
                    AssemblyComponent("joist", "تیرچه", "عدد", "(ceil(W/s)+1)×تعداد", float(joists), warning="تعداد تیرچه از عرض و فاصله محاسبه شده؛ آرایش واقعی دهانه/لبه‌ها در صورت تفاوت باید با joist_count صریح وارد شود."),
                ),
                ("length", "width", "count", "topping_thickness", "joist_spacing",
                 "joist_width", "joist_depth", "joist_count"),
                ("foam_length", "foam_width", "foam_height"),
            )
        foam_per = foam_l * foam_w * foam_h
        foam_count = ceil((area / (foam_l * foam_w)))
        foam_total = foam_count
        mesh_weight = _optional(p, "mesh_unit_weight")
        components = [
            AssemblyComponent("concrete", "بتن", "m³", "A×t رویه+تعداد تیرچه×L×b×h", concrete),
            AssemblyComponent("joist", "تیرچه", "عدد", "(ceil(W/s)+1)×تعداد", float(joists),
                              warning="تعداد تیرچه از عرض و فاصله مشتق شده؛ آرایش واقعی لبه‌ها و دهانه‌ها در صورت تفاوت نیازمند joist_count صریح است."),
            AssemblyComponent("foam", "بلوک یونولیت", "عدد", "ceil(A/(Lf×Wf))", float(foam_total),
                              warning=f"حجم اسمی هر بلوک {foam_per:g} m³"),
        ]
        missing = []
        used = ["length", "width", "count", "topping_thickness", "joist_spacing",
                "joist_width", "joist_depth", "foam_length", "foam_width", "foam_height"]
        if "joist_count" in p and p["joist_count"] not in (None, ""):
            used.append("joist_count")
        if mesh_weight is not None:
            components.append(AssemblyComponent("reinforcement_mesh", "مش/آرماتور شبکه‌ای", "kg",
                                                "A×وزن واحد مش", area * mesh_weight))
            used.append("mesh_unit_weight")
        # Reinforcement is drawing/specification dependent; never invent it.
        return AssemblyResult(
            "joist_foam_roof_assembly" if "foam" in k or "یونولیت" in k else "joist_block_roof_assembly",
            "سقف تیرچه یونولیت" if "foam" in k or "یونولیت" in k else "سقف تیرچه‌بلوک",
            tuple(components), tuple(used), tuple(missing)
        )

    raise KeyError(f"unsupported assembly: {code}")
