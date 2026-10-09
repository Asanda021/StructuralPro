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
from math import ceil, isfinite
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
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _count(p: Mapping[str, Any], name: str) -> int:
    if name not in p or p[name] in (None, ""):
        raise ValueError(f"{name} must be supplied explicitly")
    value = _n(p, name, 1)
    if not value.is_integer():
        raise ValueError(f"{name} must be an integer")
    return int(value)


def _optional(p: Mapping[str, Any], name: str) -> float | None:
    if name not in p or p[name] in (None, ""):
        return None
    return _n(p, name)


def _waste(q: float, factor: float | None) -> float:
    if factor is None:
        return q
    if not isfinite(factor):
        raise ValueError("waste_factor must be finite")
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
        L, H, t = _n(p, "length", 1e-12), _n(p, "height", 1e-12), _n(p, "thickness", 1e-12)
        openings = _n(p, "openings")
        if openings > L * H:
            raise ValueError("مساحت بازشوها نمی‌تواند از مساحت ناخالص دیوار بیشتر باشد")
        area = L * H - openings
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
        if min(bw, bh, bt, joint) <= 0:
            raise ValueError("ابعاد بلوک و ضخامت بند باید مثبت باشند")
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
        L, W = _n(p, "length", 1e-12), _n(p, "width", 1e-12)
        count = _count(p, "count")
        area = L * W * count
        topping = _n(p, "topping_thickness", 1e-12)
        spacing = _n(p, "joist_spacing", 1e-12)
        jw = _n(p, "joist_width", 1e-12)
        jd = _n(p, "joist_depth", 1e-12)
        joist_count = _optional(p, "joist_count")
        if joist_count is None:
            joist_count = ceil(W / spacing) + 1
        if joist_count is not None and (joist_count <= 0 or not float(joist_count).is_integer()):
            raise ValueError("joist_count must be a positive integer when supplied")
        joists = joist_count * count
        concrete = area * topping + joists * L * jw * jd
        foam_l = _optional(p, "foam_length")
        foam_w = _optional(p, "foam_width")
        foam_h = _optional(p, "foam_height")
        if any(v is not None and v <= 0 for v in (foam_l, foam_w, foam_h)):
            raise ValueError("ابعاد یونولیت باید مثبت باشند")
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

    if k in {"concrete_column", "column_concrete"}:
        count = _count(p, "count")
        width, depth, height = _n(p, "width", 1e-12), _n(p, "depth", 1e-12), _n(p, "height", 1e-12)
        gross = count * width * depth * height
        waste = _optional(p, "waste_factor")
        total = _waste(gross, waste)
        return AssemblyResult("concrete_column", "ستون بتنی", (
            AssemblyComponent("concrete", "بتن ستون", "m³", "تعداد×عرض×عمق×ارتفاع", total,
                              warning="پرت فقط در صورت ورود صریح waste_factor اعمال شده است."),
        ), ("count", "width", "depth", "height") + (("waste_factor",) if waste is not None else ()))

    if k in {"concrete_beam", "beam_concrete"}:
        count, length = _count(p, "count"), _n(p, "length", 1e-12)
        width, depth = _n(p, "width", 1e-12), _n(p, "depth", 1e-12)
        gross = count * length * width * depth
        waste = _optional(p, "waste_factor")
        total = _waste(gross, waste)
        components = [AssemblyComponent("concrete", "بتن تیر", "m³", "تعداد×طول×عرض×عمق", total,
                                        warning="پرت فقط در صورت ورود صریح waste_factor اعمال شده است.")]
        used = ["count", "length", "width", "depth"]
        if waste is not None:
            used.append("waste_factor")
        sides = _optional(p, "formwork_sides")
        if sides is not None:
            if sides not in (0, 1, 2):
                raise ValueError("formwork_sides must be 0, 1 or 2")
            form_area = count * length * (width + sides * depth)
            components.append(AssemblyComponent("formwork", "سطح قالب تیر", "m²",
                                                "تعداد×طول×(عرض زیر تیر+تعداد وجوه جانبی×عمق)", form_area,
                                                warning="تعداد وجوه جانبی صریحاً توسط کاربر تعیین شده است."))
            used.append("formwork_sides")
        rebar_rate = _optional(p, "rebar_kg_per_m3")
        if rebar_rate is not None:
            components.append(AssemblyComponent("reinforcement", "وزن آرماتور بر اساس مشخصات ورودی", "kg",
                                                "حجم بتن×وزن آرماتور واردشده بر m³", total * rebar_rate,
                                                warning="این نرخ باید از نقشه/مشخصات معتبر وارد شود؛ نرخ پیش‌فرض وجود ندارد."))
            used.append("rebar_kg_per_m3")
        return AssemblyResult("concrete_beam", "تیر بتنی", tuple(components), tuple(used))

    if k in {"concrete_slab", "slab_concrete"}:
        length, width, thickness = _n(p, "length", 1e-12), _n(p, "width", 1e-12), _n(p, "thickness", 1e-12)
        count = _count(p, "count")
        openings = _n(p, "openings")
        gross_area = count * length * width
        if openings > gross_area:
            raise ValueError("مساحت بازشوها نمی‌تواند از مساحت ناخالص دال بیشتر باشد")
        net_area = gross_area - openings
        gross_volume = net_area * thickness
        waste = _optional(p, "waste_factor")
        total_volume = _waste(gross_volume, waste)
        components = [
            AssemblyComponent("net_area", "مساحت خالص دال", "m²", "تعداد×طول×عرض−مساحت بازشوها", net_area),
            AssemblyComponent("concrete", "بتن دال", "m³", "مساحت خالص×ضخامت", total_volume,
                              warning="پرت فقط در صورت ورود صریح waste_factor اعمال شده است."),
        ]
        used = ["length", "width", "thickness", "count", "openings"]
        if waste is not None:
            used.append("waste_factor")
        return AssemblyResult("concrete_slab", "دال بتنی", tuple(components), tuple(used))

    if k in {"excavation", "خاکبرداری"}:
        length, width, depth = _n(p, "length", 1e-12), _n(p, "width", 1e-12), _n(p, "depth", 1e-12)
        count = _count(p, "count")
        volume = count * length * width * depth
        return AssemblyResult("excavation", "خاکبرداری", (
            AssemblyComponent("excavation", "حجم خاکبرداری", "m³", "تعداد×طول×عرض×عمق", volume),
        ), ("length", "width", "depth", "count"))

    if k in {"rebar", "reinforcement"}:
        count, length, unit_weight = _count(p, "count"), _n(p, "length", 1e-12), _n(p, "unit_weight", 1e-12)
        gross = count * length * unit_weight
        waste = _optional(p, "waste_factor")
        total = _waste(gross, waste)
        return AssemblyResult("rebar", "آرماتور", (
            AssemblyComponent("rebar_weight", "وزن آرماتور", "kg", "تعداد×طول×وزن واحد", total,
                              warning="وزن واحد و پرت باید از ورودی معتبر/مشخصات تأییدشده باشند."),
        ), ("count", "length", "unit_weight") + (("waste_factor",) if waste is not None else ()))

    if k in {"steel_member", "steel"}:
        count, length, unit_weight = _count(p, "count"), _n(p, "length", 1e-12), _n(p, "unit_weight", 1e-12)
        weight = count * length * unit_weight
        return AssemblyResult("steel_member", "عضو فولادی", (
            AssemblyComponent("steel_weight", "وزن عضو فولادی", "kg", "تعداد×طول×وزن واحد", weight),
        ), ("count", "length", "unit_weight"))

    if k in {"floor_finish", "floor_area"}:
        length, width = _n(p, "length", 1e-12), _n(p, "width", 1e-12)
        count = _count(p, "count")
        openings = _n(p, "openings")
        gross_area = count * length * width
        if openings > gross_area:
            raise ValueError("مساحت بازشوها نمی‌تواند از مساحت ناخالص کف بیشتر باشد")
        net_area = gross_area - openings
        components = [AssemblyComponent("finish_area", "مساحت خالص کف‌سازی", "m²",
                                        "تعداد×طول×عرض−مساحت بازشوها", net_area)]
        used = ["length", "width", "count", "openings"]
        consumption = _optional(p, "consumption_per_m2")
        if consumption is not None:
            components.append(AssemblyComponent("finish_material", "مصرف مصالح طبق نرخ ورودی", "unit",
                                                "مساحت خالص×مصرف واردشده بر m²", net_area * consumption,
                                                warning="واحد مصرف باید توسط کاربر/مشخصات تعیین شود."))
            used.append("consumption_per_m2")
        waste = _optional(p, "waste_factor")
        if waste is not None:
            components.append(AssemblyComponent("finish_procurement_area", "مقدار تهیه با پرت صریح", "m²",
                                                "مساحت خالص×(1+پرت)", _waste(net_area, waste)))
            used.append("waste_factor")
        return AssemblyResult("floor_finish", "کف‌سازی", tuple(components), tuple(used))

    raise KeyError(f"unsupported assembly: {code}")
