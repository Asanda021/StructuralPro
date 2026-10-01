"""IFC/BIM quantity extraction with optional local IfcOpenShell support."""
from __future__ import annotations
from typing import Any, Iterable
from pathlib import Path

def classify_objects(objects:Iterable[Any])->dict[str,int]:
    out={}
    for o in objects:
        k=str(getattr(o,"ifc_type",None) or getattr(o,"type",None) or "Unknown")
        out[k]=out.get(k,0)+1
    return out

def extract_quantities(objects:Iterable[Any])->list[dict[str,Any]]:
    rows=[]
    for o in objects:
        props=dict(getattr(o,"properties",{}) or {}); q={}
        for k in ("Length","Width","Height","Area","Volume","NetVolume","GrossVolume","Count"):
            if k in props:
                try:q[k]=float(props[k])
                except (TypeError,ValueError):pass
        rows.append({"global_id":getattr(o,"global_id",""),"ifc_type":getattr(o,"ifc_type",""),
                     "name":getattr(o,"name",""),"quantities":q})
    return rows

def read_ifc(path:str|Path)->list[dict[str,Any]]:
    try: import ifcopenshell
    except ImportError as exc: raise RuntimeError("Install ifcopenshell for local IFC parsing") from exc
    model=ifcopenshell.open(str(path)); rows=[]
    for obj in model.by_type("IfcProduct"):
        q={}
        for rel in getattr(obj,"IsDefinedBy",[]) or []:
            definition=getattr(rel,"RelatingPropertyDefinition",None)
            for prop in getattr(definition,"Quantities",[]) or []:
                name=getattr(prop,"Name","")
                for attr in ("LengthValue","AreaValue","VolumeValue","CountValue"):
                    if hasattr(prop,attr):
                        try:q[name]=float(getattr(prop,attr)); break
                        except Exception:pass
        rows.append({"global_id":obj.GlobalId,"ifc_type":obj.is_a(),"name":getattr(obj,"Name","") or "",
                     "quantities":q})
    return rows

def link_2d_3d(two_d:Iterable[dict[str,Any]],three_d:Iterable[dict[str,Any]])->list[dict[str,Any]]:
    by_id={str(x.get("global_id")):x for x in three_d if x.get("global_id")}; out=[]
    for x in two_d:
        m=by_id.get(str(x.get("global_id",""))); out.append({"two_d":x,"three_d":m,"linked":m is not None})
    return out
