"""Unified offline drawing takeoff boundary with explicit confirmation."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from core.drawings.pdf_takeoff import PDFTakeoffAdapter
from core.drawings.dwg_takeoff import DWGTakeoffEngine
from core.drawings.bim_quantities import read_ifc
from core.ai.auto_takeoff import LocalAutoTakeoff

_BIM_UNITS={"Length":"m","Area":"m2","Volume":"m3","NetVolume":"m3","GrossVolume":"m3","Count":"عدد"}

class UnifiedDrawingTakeoff:
    def __init__(self,price_resolver=None):
        self.price_resolver=price_resolver
        self.auto=LocalAutoTakeoff()

    def inspect(self,path:str|Path)->dict[str,Any]:
        p=Path(path)
        if not p.exists():
            raise FileNotFoundError(p)
        ext=p.suffix.lower()
        if ext==".pdf":
            adapter=PDFTakeoffAdapter()
            pages=adapter.inspect(p)
            candidates=adapter.text_takeoff_candidates(pages)
            scales=self.auto.auto_scale("\n".join(x.text for x in pages))
            return {
                "kind":"pdf","source":str(p),"pages":len(pages),
                "scale_candidate":scales,"candidates":candidates,
            }
        if ext in {".dwg",".dxf"}:
            engine=DWGTakeoffEngine()
            doc=engine.import_file(p)
            candidates=[]
            for layer in doc.layers:
                ents=[x for x in doc.entities if x.layer==layer]
                length=sum(float(x.data.get("length",0) or 0) for x in ents)
                area=sum(float(x.data.get("area",0) or 0) for x in ents)
                qty,unit=(length,"m") if length>0 else (
                    (area,"m2") if area>0 else (float(len(ents)),"عدد")
                )
                candidates.append({
                    "source":f"cad:{layer}","description":layer,"quantity":qty,
                    "unit":unit,"count":len(ents),"needs_confirmation":True
                })
            candidates.extend(self.auto.auto_takeoff(doc.entities))
            return {
                "kind":"cad","source":str(p),"summary":engine.summarize(doc),
                "candidates":candidates,"document":doc
            }
        if ext in {".ifc",".ifczip"}:
            rows=read_ifc(p)
            candidates=[]
            for row in rows:
                for key,value in row.get("quantities",{}).items():
                    candidates.append({
                        "source":"ifc:"+str(row.get("global_id","")),
                        "description":f'{row.get("ifc_type","")} {row.get("name","")} {key}',
                        "quantity":value,
                        "unit":_BIM_UNITS.get(key,"unknown"),
                        "needs_confirmation":True
                    })
            return {"kind":"bim","source":str(p),"objects":len(rows),"candidates":candidates}
        raise ValueError("فرمت نقشه پشتیبانی نمی‌شود؛ PDF، DWG، DXF یا IFC انتخاب کنید.")

    def candidates_to_rows(self,inspection,confirmations=None):
        confirmations=confirmations or {}
        out=[]; seen_sources=set()
        for i,row in enumerate(inspection.get("candidates",[]) or [],1):
            if confirmations and not confirmations.get(i,False):
                continue
            source=str(row.get("source") or f"drawing:{i}").strip()
            if source in seen_sources:
                raise ValueError(f"منبع متره تکراری و مستعد دوباره‌شماری: {source}")
            seen_sources.add(source)
            quantity=float(row.get("quantity",0) or 0)
            if not math.isfinite(quantity) or quantity < 0:
                raise ValueError("drawing quantity must be finite and non-negative")
            out.append({
                "source":source,
                "description":row.get("description",""),
                "quantity":quantity,
                "unit":row.get("unit",""),
                "needs_confirmation":row.get("needs_confirmation",True),
            })
        return out
