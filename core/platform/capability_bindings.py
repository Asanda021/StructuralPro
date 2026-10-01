"""Executable bindings for the common StructuralPro core."""
from __future__ import annotations
from typing import Any,Callable
from core.drawings.advanced_takeoff import depth_volume,cutout_area,legend,visual_symbol_search,dynamic_fill,ai_count,ai_map
from core.drawings.bim_quantities import classify_objects,extract_quantities,link_2d_3d
from core.drawings.dwg_takeoff import DWGTakeoffEngine,infer_takeoff_from_layers
from core.drawings.revisions import compare as compare_drawings
from core.takeoff.boq import build_boq
from core.takeoff.costing import cost_breakdown
from core.takeoff.formulas import evaluate as evaluate_formula
from core.takeoff.quantity_tools import apply_waste
from core.takeoff.transport import calculate_transport
from core.projects.health import project_health
from core.projects.package import export_package,import_package
from core.projects.revisions import compare_projects
from core.projects.statement_engine import build_statement_lines,statement_totals,payment_summary
from core.pricing.analysis import analyze as analyze_resources
from core.takeoff.indexation import adjusted_amount
from core.takeoff.ai_ready import missing_inputs,suggest_next_actions
from core.takeoff.modules import calculate_building_item,calculate_mechanical_item,calculate_electrical_item,calculate_civil_item
from core.ai.takeoff_assistant import LocalTakeoffAssistant

def _identity(*args:Any,**kwargs:Any)->Any:
    return kwargs or (args[0] if len(args)==1 else list(args))

def build_bindings()->dict[str,Callable[...,Any]]:
    assistant=LocalTakeoffAssistant()
    return {
        "cad-dxf":DWGTakeoffEngine().import_file,
        "cad-layers":lambda r:r.layers,"cad-lines":lambda r:[e for e in r.entities if e.entity_type=="LINE"],
        "cad-polylines":lambda r:[e for e in r.entities if e.entity_type in {"POLYLINE","LWPOLYLINE"}],
        "cad-arcs":lambda r:[e for e in r.entities if e.entity_type=="ARC"],
        "cad-circles":lambda r:[e for e in r.entities if e.entity_type=="CIRCLE"],
        "cad-ellipse":lambda r:[e for e in r.entities if e.entity_type=="ELLIPSE"],
        "cad-blocks":lambda r:r.block_counts,"cad-text":lambda r:r.text_labels,
        "cad-hatch":lambda r:[e for e in r.entities if e.entity_type=="HATCH"],
        "cad-dimensions":lambda r:[e for e in r.entities if e.entity_type=="DIMENSION"],
        "cad-xref":lambda r:r.xrefs,"cad-units":lambda r:r.units,
        "cad-scale":lambda drawing_length,real_length:real_length/drawing_length,
        "takeoff-depth":depth_volume,"takeoff-cutout":cutout_area,"takeoff-formula":evaluate_formula,
        "takeoff-waste":apply_waste,"takeoff-classification":ai_map,"takeoff-markup":_identity,
        "takeoff-legend":legend,"takeoff-visual-search":visual_symbol_search,"takeoff-dynamic-fill":dynamic_fill,
        "takeoff-ai-count":ai_count,"takeoff-ai-map":ai_map,
        "revision-drawing":compare_drawings,"revision-overlay":compare_drawings,
        "revision-history":lambda p:p.get("revisions",[]),"revision-quantity-delta":compare_projects,
        "bim-objects":classify_objects,"bim-quantities":extract_quantities,"bim-2d3d-link":link_2d_3d,
        "project-package":lambda data,mode="export":export_package(data) if mode=="export" else import_package(data),
        "project-health":project_health,"pricing-analysis":analyze_resources,"pricing-indexation":adjusted_amount,
        "estimate-boq":build_boq,"estimate-transport":calculate_transport,"estimate-cost-breakdown":cost_breakdown,
        "estimate-history":_identity,"estimate-change":compare_projects,
        "statement-multi":build_statement_lines,"statement-cumulative":statement_totals,
        "statement-retention":payment_summary,"statement-financial":payment_summary,
        "reports-custom":_identity,"integration-transfer":_identity,"integration-cad":infer_takeoff_from_layers,
        "ai-missing":missing_inputs,"ai-next":suggest_next_actions,"ai-qa":assistant.qa,
        "domain-structural":_identity,"domain-architectural":calculate_building_item,"domain-mechanical":calculate_mechanical_item,
        "domain-electrical":calculate_electrical_item,"domain-civil":calculate_civil_item,"domain-mep-coordination":_identity,
        "document-links":_identity,
    }
