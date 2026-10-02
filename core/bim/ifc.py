"""Deep IFC adapter: identity, properties, materials, levels, types and quantities."""
from __future__ import annotations
from pathlib import Path
from .model import BIMElement

_TYPE_MAP={"IFCBEAM":("structural","beam"),"IFCCOLUMN":("structural","column"),
"IFCSLAB":("structural","slab"),"IFCWALL":("architectural","wall"),
"IFCFOOTING":("structural","foundation"),"IFCMEMBER":("structural","member"),
"IFCROOF":("architectural","roof"),"IFCWINDOW":("architectural","window"),
"IFCDOOR":("architectural","door")}

def _props(obj):
    out={}
    for definition in getattr(obj,"IsDefinedBy",()) or ():
        try:
            rel=definition.RelatingPropertyDefinition
            for prop in getattr(rel,"HasProperties",()) or ():
                name=str(getattr(prop,"Name","") or "")
                value=getattr(prop,"NominalValue",None)
                if value is not None:
                    out[name]=getattr(value,"wrappedValue",value)
        except Exception:
            continue
    return out

def _materials(obj):
    vals=[]
    for rel in getattr(obj,"HasAssociations",()) or ():
        mat=getattr(rel,"RelatingMaterial",None)
        if mat is None: continue
        for x in getattr(mat,"ForLayerSet",None).MaterialLayers if getattr(mat,"ForLayerSet",None) else ():
            vals.append(str(getattr(x.Material,"Name","") or ""))
        name=getattr(mat,"Name",None)
        if name: vals.append(str(name))
    return tuple(dict.fromkeys(x for x in vals if x))

def _level(obj):
    for rel in getattr(obj,"ContainedInStructure",()) or ():
        st=getattr(rel,"RelatingStructure",None)
        if st and str(st.is_a()).upper()=="IFCBUILDINGSTOREY":
            return str(getattr(st,"Name","") or "")
    return None

class DeepIFCAdapter:
    extensions=(".ifc",)
    def read(self,path):
        p=Path(path)
        if not p.exists() or not p.is_file(): raise FileNotFoundError(p)
        try: import ifcopenshell
        except ImportError as exc: raise RuntimeError("Install ifcopenshell for deep BIM/IFC support") from exc
        model=ifcopenshell.open(str(p)); rows=[]
        for obj in model.by_type("IfcProduct"):
            typ=str(obj.is_a()).upper()
            mapped=_TYPE_MAP.get(typ)
            if not mapped: continue
            props=_props(obj)
            geometry={}
            for key in ("Length","Width","Height","Depth","Area","Volume","NetVolume","GrossVolume"):
                if key in props:
                    try: geometry[key.lower()]=float(props[key])
                    except (TypeError,ValueError): pass
            type_name=None
            for rel in getattr(obj,"IsTypedBy",()) or ():
                type_obj=getattr(rel,"RelatingType",None)
                if type_obj: type_name=str(getattr(type_obj,"Name","") or "") or None
            rows.append(BIMElement(
                global_id=str(obj.GlobalId),ifc_type=typ,name=str(getattr(obj,"Name","") or ""),
                domain=mapped[0],kind=mapped[1],level=_level(obj),type_name=type_name,
                material_names=_materials(obj),properties=props,geometry=geometry,
                source_id=f"ifc:{p.name}:{obj.GlobalId}"))
        return tuple(rows)
