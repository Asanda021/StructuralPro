"""Unified offline drawing takeoff service for PDF, DXF/DWG and IFC inputs."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from core.drawings.pdf_takeoff import PDFTakeoffAdapter
from core.drawings.dwg_takeoff import DWGTakeoffEngine, infer_takeoff_from_layers
from core.drawings.bim_quantities import read_ifc, extract_quantities

class UnifiedDrawingTakeoff:
    """Single user-facing boundary: import -> candidates -> confirmation -> BOQ rows."""
    def __init__(self, price_resolver=None):
        self.price_resolver = price_resolver

    def inspect(self, path: str|Path) -> dict[str,Any]:
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        ext=p.suffix.lower()
        if ext==".pdf":
            pages=PDFTakeoffAdapter().inspect(p)
            candidates=PDFTakeoffAdapter().text_takeoff_candidates(pages)
            return {"kind":"pdf","source":str(p),"pages":len(pages),"candidates":candidates}
        if ext in {".dwg",".dxf"}:
            doc=DWGTakeoffEngine().import_file(p)
            return {"kind":"cad","source":str(p),"summary":DWGTakeoffEngine().summarize(doc),"document":doc}
        if ext in {".ifc",".ifczip"}:
            rows=read_ifc(p)
            return {"kind":"bim","source":str(p),"objects":len(rows),"candidates":rows}
        raise ValueError("فرمت نقشه پشتیبانی نمی‌شود؛ PDF، DWG، DXF یا IFC انتخاب کنید.")

    def candidates_to_rows(self, inspection:dict[str,Any], confirmations:dict[int,bool]|None=None) -> list[dict[str,Any]]:
        confirmations=confirmations or {}
        out=[]
        for i,row in enumerate(inspection.get("candidates",[]) or [],1):
            if inspection.get("kind")=="pdf":
                if confirmations and not confirmations.get(i,False): continue
                out.append({"source":row["source"],"description":row["description"],"quantity":row["quantity"],
                            "unit":row["unit"],"needs_confirmation":row.get("needs_confirmation",True)})
            elif inspection.get("kind")=="bim":
                q=row.get("quantities",{})
                for key,value in q.items():
                    out.append({"source":"ifc:"+str(row.get("global_id","")),
                                "description":f'{row.get("ifc_type","")} {row.get("name","")} {key}',
                                "quantity":value,"unit":"unknown","needs_confirmation":True})
        return out
