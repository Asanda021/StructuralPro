"""Offline CAD takeoff engine with layer/block/xref aware extraction."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import math

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
    source: str=""
    format: str="DXF"

def _xy(v): return (float(v[0]),float(v[1]))

def _poly_metrics(points, closed=False):
    pts=[_xy(p) for p in points]
    if any(not math.isfinite(v) for p in pts for v in p):
        raise ValueError("CAD geometry contains non-finite coordinates")
    length=sum(math.dist(pts[i],pts[i+1]) for i in range(len(pts)-1))
    if closed and len(pts)>2: length+=math.dist(pts[-1],pts[0])
    area=0.0
    if len(pts)>2 and closed:
        area=abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))/2)
    return length,area

class DWGTakeoffEngine:
    def _read_dxf(self,p:Path)->DWGDocument:
        try: import ezdxf
        except ImportError as exc: raise RuntimeError("Install ezdxf for DXF/DWG extraction") from exc
        doc=ezdxf.readfile(str(p)); out=DWGDocument(source=str(p),format="DXF"); layers=set()
        units_map={0:"unitless",1:"in",2:"ft",3:"mi",4:"mm",5:"cm",6:"m",7:"km"}
        raw_units=int(doc.header.get("$INSUNITS",0) or 0)
        out.units=units_map.get(raw_units,"unknown")
        out.__dict__["unit_name"]=out.units
        try: out.xrefs=[str(x) for x in doc.xrefdocpaths]
        except Exception: pass
        for e in doc.modelspace():
            typ=e.dxftype(); layer=str(getattr(e.dxf,"layer","0")); layers.add(layer); data={}
            if typ=="LINE":
                data["start"]=_xy(e.dxf.start); data["end"]=_xy(e.dxf.end); data["length"]=math.dist(data["start"],data["end"])
            elif typ in {"LWPOLYLINE","POLYLINE"}:
                pts=[p[:2] for p in e.get_points("xy")] if typ=="LWPOLYLINE" else [v.dxf.location for v in e.vertices()]
                data["length"],data["area"]=_poly_metrics(pts,bool(getattr(e,"closed",False))); data["points"]=pts
            elif typ=="CIRCLE":
                r=float(e.dxf.radius); data.update(radius=r,length=2*math.pi*r,area=math.pi*r*r)
            elif typ=="ARC":
                r=float(e.dxf.radius); sweep=(float(e.dxf.end_angle)-float(e.dxf.start_angle))%360; data.update(radius=r,length=2*math.pi*r*sweep/360)
            elif typ in {"TEXT","MTEXT"}:
                data["text"]=str(e.dxf.text if hasattr(e.dxf,"text") else e.text); out.text_labels.append(data["text"])
            elif typ=="INSERT":
                name=str(e.dxf.name); out.block_counts[name]=out.block_counts.get(name,0)+1; data.update(block=name,insert=_xy(e.dxf.insert))
            elif typ=="HATCH": data["pattern"]=str(getattr(e.dxf,"pattern_name",""))
            else:
                for a in ("start","end","center","insert"):
                    if hasattr(e.dxf,a):
                        try: data[a]=_xy(getattr(e.dxf,a))
                        except Exception: pass
            out.entities.append(DWGEntity(typ,layer,getattr(e.dxf,"handle",None),data))
        factor={"in":0.0254,"ft":0.3048,"mi":1609.344,"mm":0.001,"cm":0.01,"m":1.0,"km":1000.0}.get(out.units)
        if factor is not None and factor != 1.0:
            normalized=[]
            for entity in out.entities:
                data=dict(entity.data)
                for key in ("length","radius"):
                    if key in data: data[key]=float(data[key])*factor
                if "area" in data: data["area"]=float(data["area"])*(factor**2)
                for key in ("start","end","insert","center"):
                    if key in data and data[key] is not None:
                        data[key]=(float(data[key][0])*factor,float(data[key][1])*factor)
                if "points" in data:
                    data["points"]=[(float(p[0])*factor,float(p[1])*factor) for p in data["points"]]
                normalized.append(DWGEntity(entity.entity_type,entity.layer,entity.handle,data))
            out.entities=normalized
        out.layers=sorted(layers); return out

    def import_file(self,path:str|Path)->DWGDocument:
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        if p.suffix.lower()==".dxf": return self._read_dxf(p)
        if p.suffix.lower()!=".dwg": raise ValueError("Expected .dwg or .dxf")
        from core.drawings.dwg_converter import OfflineDWGConverter
        converted=OfflineDWGConverter().convert(p).output
        doc=self._read_dxf(converted); doc.source=str(p); doc.format="DWG→DXF"
        return doc

    def summarize(self,doc:DWGDocument)->dict[str,Any]:
        by_type={}
        for e in doc.entities: by_type[e.entity_type]=by_type.get(e.entity_type,0)+1
        return {"entities":len(doc.entities),"by_type":by_type,"layers":doc.layers,"blocks":doc.block_counts,
                "text_count":len(doc.text_labels),"xrefs":doc.xrefs,"units":doc.units,"source":doc.source,"format":doc.format}

    def layer_takeoff(self,doc:DWGDocument,rules:dict[str,dict[str,Any]])->list[dict[str,Any]]:
        out=[]
        for layer,rule in rules.items():
            ents=[e for e in doc.entities if e.layer==layer]
            if not ents: continue
            metric=rule.get("metric","count"); values=[float(e.data.get(metric,1) or 0) for e in ents]
            if any(not math.isfinite(v) or v < 0 for v in values):
                raise ValueError(f"Invalid CAD quantity on layer: {layer}")
            qty=sum(values)
            out.append({"layer":layer,"count":len(ents),"quantity":qty,"description":rule.get("description",layer),
                        "unit":rule.get("unit","عدد" if metric=="count" else "m"),"price_code":rule.get("price_code"),
                        "source":f"dwg-layer:{layer}","needs_confirmation":False})
        return out

def infer_takeoff_from_layers(doc:DWGDocument,rules:dict[str,dict[str,Any]])->list[dict[str,Any]]:
    return DWGTakeoffEngine().layer_takeoff(doc,rules)
