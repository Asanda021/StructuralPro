"""End-to-end drawing -> takeoff -> mapping -> assembly -> estimate workflow."""
from __future__ import annotations
from typing import Any
from core.drawings.unified_takeoff import UnifiedDrawingTakeoff
from core.ai.takeoff_assistant import LocalTakeoffAssistant
from core.takeoff.assemblies import AssemblyLibrary

class TakeoffWorkflow:
    def __init__(self,price_catalog=None):
        self.drawing=UnifiedDrawingTakeoff(price_resolver=price_catalog)
        self.ai=LocalTakeoffAssistant()
        self.assemblies=AssemblyLibrary()
        self.catalog=price_catalog

    def inspect(self,path):
        return self.drawing.inspect(path)

    def confirm(self,inspection,selected=None):
        rows=inspection.get("candidates",[]) or []
        selected=set(range(1,len(rows)+1)) if selected is None else set(selected)
        return [dict(r,confirmed=True) for i,r in enumerate(rows,1) if i in selected]

    def map_price_codes(self,rows,catalog_rows):
        mapped=self.ai.suggest_mapping(rows,catalog_rows)
        out=[]
        for row,suggestion in zip(rows,mapped):
            x=dict(row); x["price_suggestions"]=suggestion["suggestions"]
            if suggestion["suggestions"] and not x.get("price_code"):
                x["price_code"]=suggestion["suggestions"][0].get("code")
            out.append(x)
        return out

    def apply_assembly(self,row,assembly_code):
        x=dict(row); x["assembly_code"]=assembly_code
        x["assembly"]=self.assemblies.expand(assembly_code,float(x.get("quantity",0)))
        x["assembly_total"]=sum(float(c["cost"]) for c in x["assembly"])
        return x

    def build_estimate(self,rows,price_lookup=None):
        result=[]
        for row in rows:
            x=dict(row); q=float(x.get("quantity",0))
            if q<0: raise ValueError("quantity cannot be negative")
            price=None
            if price_lookup and x.get("price_code"): price=price_lookup.get(x["price_code"])
            x["unit_price"]=float(price or x.get("unit_price") or 0)
            x["total"]=q*x["unit_price"]
            result.append(x)
        return result

    def run(self,path,catalog_rows=None,selected=None,price_lookup=None):
        inspection=self.inspect(path)
        confirmed=self.confirm(inspection,selected)
        mapped=self.map_price_codes(confirmed,catalog_rows or [])
        estimated=self.build_estimate(mapped,price_lookup)
        return {"inspection":inspection,"rows":estimated,
                "summary":{"items":len(estimated),"total":sum(x["total"] for x in estimated)}}

