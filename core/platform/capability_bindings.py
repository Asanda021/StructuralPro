"""Executable bindings for StructuralPro capabilities."""
from __future__ import annotations
from typing import Any, Callable
from core.drawings.advanced_takeoff import (
    depth_volume, cutout_area, legend, visual_symbol_search, dynamic_fill,
    ai_count, ai_map, length_takeoff, area_takeoff, count_takeoff, perimeter_takeoff,
)
from core.drawings.bim_quantities import classify_objects, extract_quantities, link_2d_3d
from core.drawings.dwg_takeoff import DWGTakeoffEngine, infer_takeoff_from_layers
from core.drawings.revisions import compare as compare_drawings
from core.takeoff.boq import build_boq
from core.takeoff.costing import cost_breakdown
from core.takeoff.formulas import evaluate as evaluate_formula
from core.takeoff.quantity_tools import apply_waste
from core.takeoff.transport import calculate_transport
from core.takeoff.modules import calculate_building_item, calculate_mechanical_item, calculate_electrical_item, calculate_civil_item
from core.ai.takeoff_assistant import LocalTakeoffAssistant
from core.projects.workflow import project_health, audit_project, save_template, export_package, backup_project, copy_project
from core.takeoff.estimate_history import snapshot as estimate_snapshot, delta as estimate_delta
from core.reports.custom import build_custom_report

def _identity(*args: Any, **kwargs: Any) -> Any:
    return kwargs or (args[0] if len(args) == 1 else list(args))

def _missing_inputs(project: Any) -> list[dict[str, str]]:
    if not isinstance(project, dict):
        return [{"code": "invalid_project", "message": "پروژه باید به صورت شیء داده‌ای باشد."}]
    return [{"code": "missing_project_name", "message": "نام پروژه وارد نشده است."}] if not str(project.get("name", "")).strip() else []

def _suggest_next_actions(project: Any) -> list[str]:
    return ["تکمیل اطلاعات پروژه", "اجرای متره", "تطبیق با فهرست‌بها", "بازبینی هشدارها"]

def build_bindings() -> dict[str, Callable[..., Any]]:
    assistant = LocalTakeoffAssistant()
    return {
        "cad-dxf": DWGTakeoffEngine().import_file,
        "cad-layers": lambda r: r.layers,
        "cad-lines": lambda r: [e for e in r.entities if e.entity_type == "LINE"],
        "cad-polylines": lambda r: [e for e in r.entities if e.entity_type in {"POLYLINE", "LWPOLYLINE"}],
        "cad-arcs": lambda r: [e for e in r.entities if e.entity_type == "ARC"],
        "cad-circles": lambda r: [e for e in r.entities if e.entity_type == "CIRCLE"],
        "cad-ellipse": lambda r: [e for e in r.entities if e.entity_type == "ELLIPSE"],
        "cad-blocks": lambda r: r.block_counts,
        "cad-text": lambda r: r.text_labels,
        "cad-hatch": lambda r: [e for e in r.entities if e.entity_type == "HATCH"],
        "cad-dimensions": lambda r: [e for e in r.entities if e.entity_type == "DIMENSION"],
        "cad-xref": lambda r: r.xrefs,
        "cad-units": lambda r: r.units,
        "cad-scale": lambda drawing_length, real_length: real_length / drawing_length,
        "takeoff-length": length_takeoff,
        "takeoff-area": area_takeoff,
        "takeoff-count": count_takeoff,
        "takeoff-perimeter": perimeter_takeoff,
        "takeoff-volume": depth_volume,
        "takeoff-depth": depth_volume,
        "takeoff-cutout": cutout_area,
        "takeoff-formula": evaluate_formula,
        "takeoff-waste": apply_waste,
        "takeoff-markup": _identity,
        "takeoff-legend": legend,
        "takeoff-visual-search": visual_symbol_search,
        "takeoff-dynamic-fill": dynamic_fill,
        "takeoff-ai-count": ai_count,
        "takeoff-ai-map": ai_map,
        "revision-drawing": compare_drawings,
        "revision-overlay": compare_drawings,
        "revision-quantity-delta": estimate_delta,
        "bim-objects": classify_objects,
        "bim-quantities": extract_quantities,
        "bim-2d3d-link": link_2d_3d,
        "estimate-boq": build_boq,
        "estimate-transport": calculate_transport,
        "estimate-cost-breakdown": cost_breakdown,
        "estimate-history": estimate_snapshot,
        "estimate-change": estimate_delta,
        "integration-cad": infer_takeoff_from_layers,
        "ai-missing": _missing_inputs,
        "ai-next": _suggest_next_actions,
        "ai-qa": assistant.qa,
        "project-templates": save_template,
        "project-library": lambda project: project,
        "project-package": export_package,
        "project-backup": backup_project,
        "project-audit": audit_project,
        "project-health": project_health,
        "reports-custom": build_custom_report,
        "domain-structural": _identity,
        "domain-architectural": calculate_building_item,
        "domain-mechanical": calculate_mechanical_item,
        "domain-electrical": calculate_electrical_item,
        "domain-civil": calculate_civil_item,
        "domain-mep-coordination": _identity,
        "document-links": _identity,
    }
