"""Explicit-input assembly templates for professional quantity takeoff.

Templates only describe required user inputs. They never supply hidden dimensions,
waste percentages, material ratios, or unit prices. Calculation is delegated to
the deterministic assembly engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.takeoff.assembly import AssemblyResult, calculate_assembly


@dataclass(frozen=True)
class AssemblyTemplate:
    code: str
    title_fa: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()


TEMPLATES: tuple[AssemblyTemplate, ...] = (
    AssemblyTemplate("block_wall", "دیوار بلوکی",
                     ("length", "height", "thickness", "openings", "block_length", "block_height",
                      "block_thickness", "joint_thickness", "cement_parts", "sand_parts"),
                     ("block_waste_factor", "mortar_waste_factor")),
    AssemblyTemplate("joist_foam_roof_assembly", "سقف تیرچه یونولیت",
                     ("count", "length", "width", "topping_thickness", "joist_spacing", "joist_width",
                      "joist_depth", "foam_length", "foam_width", "foam_height"),
                     ("joist_count", "mesh_unit_weight")),
    AssemblyTemplate("joist_block_roof_assembly", "سقف تیرچه‌بلوک",
                     ("count", "length", "width", "topping_thickness", "joist_spacing", "joist_width",
                      "joist_depth", "foam_length", "foam_width", "foam_height"),
                     ("joist_count", "mesh_unit_weight")),
    AssemblyTemplate("concrete_column", "ستون بتنی", ("count", "width", "depth", "height"), ("waste_factor",)),
    AssemblyTemplate("concrete_beam", "تیر بتنی", ("count", "length", "width", "depth"),
                     ("waste_factor", "formwork_sides", "rebar_kg_per_m3")),
    AssemblyTemplate("concrete_slab", "دال بتنی", ("count", "length", "width", "thickness", "openings"),
                     ("waste_factor",)),
    AssemblyTemplate("excavation", "خاکبرداری", ("count", "length", "width", "depth")),
    AssemblyTemplate("rebar", "آرماتور", ("count", "length", "unit_weight"), ("waste_factor",)),
    AssemblyTemplate("steel_member", "عضو فولادی", ("count", "length", "unit_weight"), ()),
    AssemblyTemplate("floor_finish", "کف‌سازی", ("count", "length", "width", "openings"),
                     ("consumption_per_m2", "consumption_unit", "waste_factor")),
)


class AssemblyTemplateLibrary:
    """Read-only template catalog with strict, fail-closed input validation."""

    def __init__(self, templates: tuple[AssemblyTemplate, ...] = TEMPLATES):
        templates = tuple(templates)
        items = {item.code: item for item in templates}
        if len(items) != len(templates):
            raise ValueError("کد قالب متره تکراری است")
        self._items = items

    def list(self) -> tuple[AssemblyTemplate, ...]:
        return tuple(self._items.values())

    def get(self, code: str) -> AssemblyTemplate:
        try:
            return self._items[str(code).strip()]
        except KeyError as exc:
            raise KeyError(f"قالب متره ناشناخته است: {code}") from exc

    def expand(self, code: str, inputs: Mapping[str, Any]) -> AssemblyResult:
        template = self.get(code)
        missing = tuple(name for name in template.required_inputs
                        if name not in inputs or inputs[name] in (None, ""))
        if missing:
            return AssemblyResult(template.code, template.title_fa, (), (), missing)
        # Pass only explicitly supplied values. No template default becomes a quantity.
        result = calculate_assembly(template.code, **dict(inputs))
        if result.missing_inputs:
            return AssemblyResult(template.code, template.title_fa, result.components,
                                  result.inputs_used, result.missing_inputs)
        return result
