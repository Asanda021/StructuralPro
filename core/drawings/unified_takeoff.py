"""Unified offline drawing takeoff boundary with explicit confirmation."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from core.drawings.pdf_takeoff import PDFTakeoffAdapter
from core.drawings.dwg_takeoff import DWGTakeoffEngine
from core.drawings.bim_quantities import read_ifc
_BIM_UNITS={"Length":"m","Area":"m2","Volume":"m3","NetVolume":"m3","GrossVolume":"m3","Count":"عدد"}
class UnifiedDrawingTakeoff:
    def __init__(self,price_resolver=None): self.price_resolver=price_resolver
    def inspect(self,path:str|Path)->dict[str,Any]:
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        ext=p.suffix.lower()
        if ext==".pdf":
            a=PDFTakeoffAdapter(); pages=a.inspect(p)
            return {"kind":"pdf","source":str(p),"pages":len(pages),"candidates":a.text_takeoff_candidates(pages)}
        if ext in {".dwg",".dxf"}:
            e=DWGTakeoffEngine(); doc=e.import_file(p); candidates=[]
            for layer in doc.layers:
                ents=[x for x in doc.entities if x.layer==layer]
                length=sum(float(x.data.get("length",0) or 0) for x in ents)
                area=sum(float(x.data.get("area",0) or 0) for x in ents)
                qty,unit=(length,"m") if length>0 else ((area,"m2") if area>0 else (float(len(ents)),"عدد"))
                candidates.append({"source":f"cad:{layer}","description":layer,"quantity":qty,"unit":unit,
                                   "count":len(ents),"needs_confirmation":True})
            return {"kind":"cad","source":str(p),"summary":e.summarize(doc),"candidates":candidates,"document":doc}
        if ext in {".ifc",".ifczip"}:
            rows=read_ifc(p); candidates=[]
            for row in rows:
                for key,value in row.get("quantities",{}).items():
                    candidates.append({"source":"ifc:"+str(row.get("global_id","")),
                        "description":f'{row.get("ifc_type","")} {row.get("name","")} {key}',
                        "quantity":value,"unit":_BIM_UNITS.get(key,"unknown"),"needs_confirmation":True})
            return {"kind":"bim","source":str(p),"objects":len(rows),"candidates":candidates}
        raise ValueError("فرمت نقشه پشتیبانی نمی‌شود؛ PDF، DWG، DXF یا IFC انتخاب کنید.")
    def candidates_to_rows(self,inspection,confirmations=None):
        confirmations=confirmations or {}
        out=[]
        for i,row in enumerate(inspection.get("candidates",[]) or [],1):
            if confirmations and not confirmations.get(i,False): continue
            if float(row.get("quantity",0) or 0)<0: raise ValueError("drawing quantity cannot be negative")
            out.append({"source":row.get("source","drawing"),"description":row.get("description",""),
                        "quantity":float(row.get("quantity",0) or 0),"unit":row.get("unit",""),
                        "needs_confirmation":False if confirmations else row.get("needs_confirmation",True)})
        return out
