from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class DWGEntity:
    entity_type: str
    layer: str
    handle: str | None
    data: dict[str, Any]

@dataclass
class DWGDocument:
    entities: list[DWGEntity] = field(default_factory=list)
    layers: list[str] = field(default_factory=list)
    block_counts: dict[str,int] = field(default_factory=dict)
    text_labels: list[str] = field(default_factory=list)
    xrefs: list[str] = field(default_factory=list)
    units: str = "unknown"

class DWGTakeoffEngine:
    def import_file(self, path: str | Path) -> DWGDocument:
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        if p.suffix.lower() not in {".dxf",".dwg"}: raise ValueError("Expected DWG or DXF")
        if p.suffix.lower()==".dwg":
            raise RuntimeError("Native DWG parsing requires a local converter; export to DXF for fully offline parsing")
        try: import ezdxf
        except ImportError as exc: raise RuntimeError("Install ezdxf for DXF import") from exc
        doc=ezdxf.readfile(str(p)); out=DWGDocument(); layers=set()
        out.units=str(getattr(doc.header,"$INSUNITS","unknown"))
        for e in doc.modelspace():
            layer=str(getattr(e.dxf,"layer","0")); layers.add(layer); data={}
            for a in ("start","end","center","radius","text","insert"):
                if hasattr(e,a):
                    v=getattr(e,a)
                    try: data[a]=tuple(v)
                    except TypeError: data[a]=v
            out.entities.append(DWGEntity(e.dxftype(),layer,getattr(e.dxf,"handle",None),data))
            if e.dxftype() in {"TEXT","MTEXT"}: out.text_labels.append(str(getattr(e.dxf,"text","")))
        out.layers=sorted(layers)
        return out

def infer_takeoff_from_layers(doc: DWGDocument, rules: dict[str,dict[str,Any]]) -> list[dict[str,Any]]:
    result=[]
    for layer,rule in rules.items():
        ents=[e for e in doc.entities if e.layer==layer]
        if ents: result.append({"layer":layer,"count":len(ents),"description":rule.get("description",layer),"unit":rule.get("unit","count"),"price_code":rule.get("price_code")})
    return result
