"""Unified offline drawing takeoff service for PDF, DXF/DWG and IFC inputs."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from core.drawings.pdf_takeoff import PDFTakeoffAdapter
from core.drawings.dwg_takeoff import DWGTakeoffEngine
from core.drawings.bim_quantities import read_ifc

_BIM_UNITS={"Length":"m","Area":"m2","Volume":"m3","NetVolume":"m3","GrossVolume":"m3","Count":"عدد"}

class UnifiedDrawingTakeoff:
    """Single user-facing boundary: import -> candidates -> confirmation -> BOQ rows."""
    def __init__(self, price_resolver=None):
        self.price_resolver=price_resolver

    def inspect(self,path:str|Path)->dict[str,Any]:
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        ext=p.suffix.lower()
        if ext==".pdf":
            adapter=PDFTakeoffAdapter(); pages=adapter.inspect(p)
            return {"kind":"pdf","source":str(p),"pages":len(pages),
                    "candidates":adapter.text_takeoff_candidates(pages)}
        if ext in {".dwg",".dxf"}:
            engine=DWGTakeoffEngine(); doc=engine.import_file(p)
            candidates=[]
            for layer in doc.layers:
                ents=[e for e in doc.entities if e.layer==layer]
                length=sum(float(e.data.get("length",0) or 0) for e in ents)
                area=sum(float(e.data.get("area",0) or 0) for e in ents)
                if length>0: qty,unit=length,"m"
                elif area>0: qty,unit=area,"m2"
                else: qty,unit=float(len(ents)),"عدد"
                candidates.append({"source":f"cad:{layer}","description":layer,
                                   "quantity":qty,"unit":unit,"count":len(ents),
                                   "needs_confirmation":True})
            return {"kind":"cad","source":str(p),"summary":engine.summarize(doc),"candidates":candidates,"document":doc}
        if ext in {".ifc",".ifczip"}:
            rows=read_ifc(p)
            candidates=[]
            for row in rows:
                for key,value in row.get("quantities",{}).items():
                    candidates.append({"source":"ifc:"+str(row.get("global_id","")),
                        "description":f'{row.get("ifc_type","")} {row.get("name","")} {key}',
                        "quantity":value,"unit":_BIM_UNITS.get(key,"unknown"),"needs_confirmation":True})
            return {"kind":"bim","source":str(p),"objects":len(rows),"candidates":candidates}
        raise ValueError("فرمت نقشه پشتیبانی نمی‌شود؛ PDF، DWG، DXF یا IFC انتخاب کنید.")

    def candidates_to_rows(self,inspection:dict[str,Any],confirmations:dict[int,bool]|None=None)->list[dict[str,Any]]:
        confirmations=confirmations or {}
        out=[]
        for i,row in enumerate(inspection.get("candidates",[]) or [],1):
            if confirmations and not confirmations.get(i,False): continue
            out.append({"source":row.get("source","drawing"),"description":row.get("description",""),
                        "quantity":float(row.get("quantity",0) or 0),"unit":row.get("unit",""),
                        "needs_confirmation":row.get("needs_confirmation",True)})
        return out
