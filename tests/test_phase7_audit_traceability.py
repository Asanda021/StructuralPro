import pytest

from core.audit.traceability import (
    AuditEvent, AuditTrail, TraceNode, TraceGraph, audit_report,
    build_trace_graph, stable_id,
)
from core.pricing.engine import CoefficientEngine, CoefficientRule

def test_whole_project_trace_chain_is_domain_neutral():
    nodes = []
    previous = None
    for stage in ("drawing", "model", "takeoff", "boq", "estimate", "revision"):
        node = TraceNode("", stage, discipline="architecture", source="cad",
                         external_id=f"A-{stage}", revision="R02", quantity=10, unit="m2")
        nodes.append(node.as_dict())
    ids = [x["node_id"] for x in nodes]
    graph = build_trace_graph(nodes, list(zip(ids, ids[1:])))
    assert graph.validate()["valid"] is True
    assert graph.lineage(ids[-1]) == ids[:-1]

def test_multiple_disciplines_share_same_trace_contract():
    nodes = [
        TraceNode("", "drawing", "architecture", "cad", "A1").as_dict(),
        TraceNode("", "model", "structural", "ifc", "S1").as_dict(),
        TraceNode("", "takeoff", "steel", "ifc", "ST1").as_dict(),
        TraceNode("", "boq", "masonry", "manual", "M1").as_dict(),
        TraceNode("", "estimate", "mechanical", "spec", "MEP1").as_dict(),
    ]
    graph = build_trace_graph(nodes)
    assert graph.validate()["valid"] is True

def test_duplicate_detection_prevents_double_counting():
    n1 = TraceNode("", "takeoff", "architecture", "cad", "W1").as_dict()
    n2 = TraceNode("", "takeoff", "architecture", "cad", "W1").as_dict()
    graph = TraceGraph()
    graph.add_node(n1 and TraceNode(**n1))
    with pytest.raises(ValueError):
        graph.add_node(TraceNode(**n2))

def test_audit_events_are_immutable_and_unique():
    trail = AuditTrail()
    event = AuditEvent("E1", "update", "N1", user="engineer", timestamp="2026-10-02T10:00:00Z")
    trail.append(event)
    with pytest.raises(ValueError):
        trail.append(event)
    assert trail.for_node("N1")[0]["user"] == "engineer"

def test_coefficient_engine_is_explicit_and_scoped():
    engine = CoefficientEngine([
        CoefficientRule("overhead", 0.10, scope="project", discipline="architecture",
                        source="official", reason="contract"),
        CoefficientRule("waste", 0.05, scope="project", discipline="architecture",
                        source="project", reason="material waste"),
        CoefficientRule("steel_only", 0.20, scope="item", discipline="steel", item_code="S1",
                        source="custom"),
    ])
    result = engine.calculate(100, discipline="architecture")
    assert result["result"] == pytest.approx(115)
    assert len(result["applied"]) == 2
    assert len(engine.applicable(discipline="architecture")) == 2

def test_audit_report_contains_lineage_and_events():
    graph = TraceGraph()
    graph.add_node(TraceNode("D1", "drawing", "architecture", "cad", "A1"))
    graph.add_node(TraceNode("T1", "takeoff", "architecture", "cad", "T1"))
    graph.link("D1", "T1")
    trail = AuditTrail([AuditEvent("E1", "create", "D1", user="u", timestamp="2026-10-02T10:00:00Z")])
    report = audit_report(graph, trail)
    assert report["valid"] is True
    assert report["edges"] == [{"from":"D1","to":"T1"}]
    assert report["audit_events"][0]["action"] == "create"
