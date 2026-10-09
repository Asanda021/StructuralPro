import io
import pytest

ifc = pytest.importorskip("ifcopenshell")

from core.bim.phase22 import IFCError, extract_ifc, fingerprint, validate_model, element_to_takeoff


def sample_ifc():
    model = ifc.file(schema="IFC4")
    project = model.create_entity("IfcProject", GlobalId="3fJ8$abc1234567890123", Name="Demo")
    unit = model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Prefix="MILLI", Name="METRE")
    model.create_entity("IfcUnitAssignment", Units=[unit])
    project.UnitsInContext = next(iter(model.by_type("IfcUnitAssignment")), None)
    wall = model.create_entity("IfcWall", GlobalId="3fJ8$wall123456789012", Name="Wall-01")
    prop = model.create_entity("IfcPropertySingleValue", Name="Material", NominalValue=model.create_entity("IfcLabel", "Concrete"))
    pset = model.create_entity("IfcPropertySet", GlobalId="3fJ8$pset123456789012", Name="Pset_WallCommon", HasProperties=[prop])
    rel = model.create_entity("IfcRelDefinesByProperties", GlobalId="3fJ8$rel123456789012", RelatedObjects=[wall], RelatingPropertyDefinition=pset)
    q = model.create_entity("IfcQuantityVolume", Name="NetVolume", VolumeValue=12.5)
    qset = model.create_entity("IfcElementQuantity", GlobalId="3fJ8$qset123456789012", Name="BaseQuantities", Quantities=[q])
    model.create_entity("IfcRelDefinesByProperties", GlobalId="3fJ8$qrel123456789012", RelatedObjects=[wall], RelatingPropertyDefinition=qset)
    stream = io.BytesIO()
    stream.write(model.to_string().encode("utf-8"))
    return stream.getvalue()


def test_ifc_extracts_elements_properties_quantities():
    result = extract_ifc(sample_ifc())
    assert result.schema == "IFC4"
    assert result.element_count == 1
    assert result.elements[0].ifc_type == "IfcWall"
    assert dict(result.elements[0].quantities)["NetVolume"] == 12.5


def test_quantity_bridge_and_fingerprint():
    raw = sample_ifc()
    result = extract_ifc(raw)
    validate_model(result)
    takeoff = element_to_takeoff(result)
    assert takeoff[0]["element_id"]
    assert takeoff[0]["quantities"]["NetVolume"] == 12.5
    assert result.export_payload()["source_fingerprint"] == fingerprint(raw)


@pytest.mark.parametrize("payload", [b"not-ifc", b"ISO-10303-21;", b"\xff\xfe"])
def test_invalid_ifc_fails_closed(payload):
    with pytest.raises(IFCError, match="decoding"):
        extract_ifc(payload)
