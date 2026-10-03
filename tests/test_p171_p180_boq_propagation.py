from core.drawing.boq_propagation_v1 import BOQPropagationWorkflow, BOQLineage
from core.drawing.takeoff_traceability_v1 import QuantityEvidence

def q(qid="q1",qty=10.0,unit="m",src=("s1",),status="accepted"):
    return QuantityEvidence(qid,"B1",src,qty,unit,.95,"formula",status).validate()

def test_builds_auditable_boq_line():
    out=BOQPropagationWorkflow().build([q()], [{"quantity_id":"q1","description":"Beam concrete"}])
    assert len(out)==1 and out[0].source_ids==("s1",)

def test_low_confidence_is_review():
    out=BOQPropagationWorkflow().build([q()], [{"quantity_id":"q1","description":"Beam","confidence":.5}])
    assert out[0].status=="review"

def test_missing_source_rejects_line():
    out=BOQPropagationWorkflow().build([q(src=())], [{"quantity_id":"q1","description":"Beam"}])
    assert out[0].status=="rejected"

def test_revision_quantity_impact():
    w=BOQPropagationWorkflow()
    old=w.build([q(qty=10)], [{"quantity_id":"q1","description":"Beam"}])
    new=w.build([q(qty=12)], [{"quantity_id":"q1","description":"Beam"}])
    assert w.impact(old,new)[0].impact=="quantity_changed"

def test_removed_line_is_explicit():
    old=(BOQLineage("b1","q1","B1",("s1",),"Beam",10,"m"),)
    assert BOQPropagationWorkflow.impact(old,())[0].impact=="removed"

def test_deterministic_order():
    w=BOQPropagationWorkflow()
    out=w.build([q("q2"),q("q1")],[{"quantity_id":"q2","description":"Z"},{"quantity_id":"q1","description":"A"}])
    assert [x.boq_id for x in out]==sorted(x.boq_id for x in out)

def test_p161_lineage_preserved():
    out=BOQPropagationWorkflow().build([q()], [{"quantity_id":"q1","description":"Beam"}])
    assert out[0].quantity_id=="q1"
