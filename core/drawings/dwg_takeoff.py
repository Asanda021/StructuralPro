"""Offline DWG/DXF takeoff engine.
DXF is parsed directly with ezdxf. Native DWG is intentionally routed through
an installed converter (for example ODA File Converter) so the core stays
offline and does not require a cloud service.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import math, os, shutil, subprocess, tempfile

@dataclass(frozen=True)
class DWGEntity:
    entity_type: str
    layer: str
    handle: str | None
    data: dict[str, Any]

@dataclass
class DWGDocument:
    entities: list[DWGEntity]=field(default_factory=list)
    layers: list[str]=field(default_factory=list)
    block_counts: dict[str,int]=field(default_factory=dict)
    text_labels: list[str]=field(default_factory=list)
    xrefs: list[str]=field(default_factory=list)
    units: str="unknown"

def _xy(v):
    return (float(v[0]),float(v[1]))

def _poly_metrics(points, closed=False):
    pts=[_xy(p) for p in points]
    length=sum(math.dist(pts[i],pts[i+1]) for i in range(len(pts)-1))
    if closed and len(pts)>2: length+=math.dist(pts[-1],pts[0])
    area=0.0
    if len(pts)>2 and closed:
        area=abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))/2)
    return length,area

class DWGTakeoffEngine:
    def _read_dxf(self,p:Path)->DWGDocument:
        try: import ezdxf
        except ImportError as exc: raise RuntimeError("Install ezdxf for DXF/DWG conversion output") from exc
        doc=ezdxf.readfile(str(p)); out=DWGDocument(); layers=set()
        out.units=str(doc.header.get("$INSUNITS","unknown"))
        try: out.xrefs=[str(x) for x in doc.xrefdocpaths]
        except Exception: pass
        for e in doc.modelspace():
            typ=e.dxftype(); layer=str(getattr(e.dxf,"layer","0")); layers.add(layer); data={}
            if typ=="LINE":
                data["start"]=_xy(e.dxf.start); data["end"]=_xy(e.dxf.end); data["length"]=math.dist(data["start"],data["end"])
            elif typ in {"LWPOLYLINE","POLYLINE"}:
                pts=[p[:2] for p in e.get_points("xy")] if typ=="LWPOLYLINE" else [v.dxf.location for v in e.vertices()]
                data["length"],data["area"]=_poly_metrics(pts,bool(getattr(e,"closed",False)))
                data["points"]=pts
            elif typ=="CIRCLE":
                r=float(e.dxf.radius); data["radius"]=r; data["length"]=2*math.pi*r; data["area"]=math.pi*r*r
            elif typ=="ARC":
                r=float(e.dxf.radius); sweep=(float(e.dxf.end_angle)-float(e.dxf.start_angle))%360
                data["radius"]=r; data["length"]=2*math.pi*r*sweep/360
            elif typ=="ELLIPSE":
                data["major_axis"]=_xy(e.dxf.major_axis); data["ratio"]=float(e.dxf.ratio)
            elif typ in {"TEXT","MTEXT"}:
                data["text"]=str(e.dxf.text if hasattr(e.dxf,"text") else e.text)
                out.text_labels.append(data["text"])
            elif typ=="INSERT":
                name=str(e.dxf.name); out.block_counts[name]=out.block_counts.get(name,0)+1
                data["block"]=name; data["insert"]=_xy(e.dxf.insert)
            elif typ=="HATCH":
                data["pattern"]=str(getattr(e.dxf,"pattern_name",""))
            else:
                for a in ("start","end","center","insert"):
                    if hasattr(e.dxf,a):
                        try: data[a]=_xy(getattr(e.dxf,a))
                        except Exception: pass
            out.entities.append(DWGEntity(typ,layer,getattr(e.dxf,"handle",None),data))
        out.layers=sorted(layers); return out

    def import_file(self,path:str|Path)->DWGDocument:
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        if p.suffix.lower()==".dxf": return self._read_dxf(p)
        if p.suffix.lower()!=".dwg": raise ValueError("Expected .dwg or .dxf")
        converted=self._convert_dwg(p)
        return self._read_dxf(converted)

    def _convert_dwg(self,p:Path)->Path:
        converter=os.getenv("STRUCTURALPRO_DWG_CONVERTER") or shutil.which("dwg2dxf") or shutil.which("ODAFileConverter")
        if not converter: raise RuntimeError("Native DWG needs an installed offline converter. Set STRUCTURALPRO_DWG_CONVERTER.")
        temp=Path(tempfile.mkdtemp(prefix="structuralpro_dwg_"))
        if Path(converter).name.lower().startswith("odafileconverter"):
            outdir=temp/"out"; outdir.mkdir()
            proc=subprocess.run([converter,str(p.parent),str(outdir),"ACAD2018","DXF","0","1","*.dwg"],capture_output=True,text=True)
            if proc.returncode: raise RuntimeError(proc.stderr or "DWG conversion failed")
            matches=list(outdir.glob("*.dxf"))
        else:
            target=temp/(p.stem+".dxf")
            proc=subprocess.run([converter,str(p),str(target)],capture_output=True,text=True)
            if proc.returncode: raise RuntimeError(proc.stderr or "DWG conversion failed")
            matches=[target]
        if not matches: raise RuntimeError("DWG converter produced no DXF")
        return matches[0]

    def summarize(self,doc:DWGDocument)->dict[str,Any]:
        return {"entities":len(doc.entities),"layers":doc.layers,"blocks":doc.block_counts,
                "text_count":len(doc.text_labels),"xrefs":doc.xrefs,"units":doc.units}

def infer_takeoff_from_layers(doc:DWGDocument,rules:dict[str,dict[str,Any]])->list[dict[str,Any]]:
    result=[]
    for layer,rule in rules.items():
        ents=[e for e in doc.entities if e.layer==layer]
        if not ents: continue
        qty=sum(float(e.data.get(rule.get("metric","count"),1)) for e in ents)
        result.append({"layer":layer,"count":len(ents),"quantity":qty,
                       "description":rule.get("description",layer),"unit":rule.get("unit","count"),
                       "price_code":rule.get("price_code"),"needs_confirmation":False})
    return result
