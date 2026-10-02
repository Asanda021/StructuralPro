import pytest
from core.drawing.measurement import primitive_measurements,scale_from_metadata,scale_from_unit
from core.drawing.models import DrawingPrimitive
from core.drawing.pipeline import DrawingMeasurementGate

def test_millimetre_drawing_is_converted_to_metres():
    result=primitive_measurements((DrawingPrimitive("line",x=0,y=0,x2=6000,y2=0,source_id="L1"),),scale_from_unit("mm"))
    assert result[0].value==pytest.approx(6.0); assert result[0].unit=="m"

def test_scale_metadata_is_explicit():
    scale=scale_from_metadata({"unit":"m","scale_denominator":100})
    assert scale.coordinate_to_m==pytest.approx(100.0); assert scale.source=="source-metadata"

def test_unknown_unit_does_not_get_assumed():
    assert scale_from_metadata({"layer":"BEAM"}) is None

def test_invalid_unit_fails_closed():
    with pytest.raises(ValueError): scale_from_unit("banana")

def test_gate_requires_explicit_scale(tmp_path):
    class FakeAdapter:
        extensions=(".fake",)
        def read(self,path):
            from core.drawing.adapters import AdapterResult,DrawingSource
            return AdapterResult(DrawingSource(tmp_path/"x.fake","fake",{}),(DrawingPrimitive("line",x=0,y=0,x2=5000,y2=0,layer="BEAM",source_id="beam:1"),))
    from core.drawing.adapters import DrawingAdapterRegistry
    gate=DrawingMeasurementGate(DrawingAdapterRegistry(adapters=(FakeAdapter(),)))
    _,scale,elements,warnings=gate.measure(str(tmp_path/"x.fake"))
    assert scale is None and elements==() and warnings

def test_gate_uses_explicit_unit(tmp_path):
    class FakeAdapter:
        extensions=(".fake",)
        def read(self,path):
            from core.drawing.adapters import AdapterResult,DrawingSource
            return AdapterResult(DrawingSource(tmp_path/"x.fake","fake",{}),(DrawingPrimitive("line",x=0,y=0,x2=5000,y2=0,layer="BEAM",source_id="beam:1"),))
    from core.drawing.adapters import DrawingAdapterRegistry
    gate=DrawingMeasurementGate(DrawingAdapterRegistry(adapters=(FakeAdapter(),)))
    _,scale,elements,warnings=gate.measure(str(tmp_path/"x.fake"),unit="mm")
    assert scale is not None and not warnings
    assert elements[0].geometry["length"]==pytest.approx(5.0)
