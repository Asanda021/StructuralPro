"""Application service shared by desktop and future mobile/chat clients."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from core.projects.store import ProjectStore
from core.takeoff.engine import TakeoffEngine
from core.takeoff.boq import build_boq, boq_summary
from core.takeoff.estimate import build_estimate
from core.commercial.progress import build_progress
from core.reports.project_report import build_report
from core.ai.qa_engine import ProjectQA

class StructuralProApp:
    def __init__(self,data_dir: str|Path):
        self.data_dir=Path(data_dir); self.data_dir.mkdir(parents=True,exist_ok=True)
        self.store=ProjectStore(self.data_dir/"projects.db")
        self.takeoff=TakeoffEngine()
        self.qa=ProjectQA()

    def create_project(self,name:str,project_id:str)->dict[str,Any]:
        project={"id":project_id,"name":name,"takeoffs":[],"boq":[],"metadata":{"offline":True}}
        self.store.save(project_id,project); return self.store.get(project_id)

    def open_project(self,project_id:str)->dict[str,Any]|None: return self.store.get(project_id)

    def add_takeoff(self,project_id:str,domain:str,item:str,**params)->dict[str,Any]:
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        result=self.takeoff.calculate(domain,item,**params)
        row={"id":f"{len(p['takeoffs'])+1}","member_code":str(params.get("member_code",item)),
             "description":item,"quantities":[{"code":item,"title":item,"unit":result.unit,"amount":result.quantity,
             "formula":result.formula,"warning":result.warning,"price_code":params.get("price_code"),"unit_price":params.get("unit_price")}]}
        p["takeoffs"].append(row)
        boq_inputs=[]
        for takeoff in p["takeoffs"]:
            for q in takeoff.get("quantities",[]):
                boq_inputs.append({"source":"manual","description":q.get("title",""),"quantity":q.get("amount",0),
                                   "unit":q.get("unit",""),"price_code":q.get("price_code"),
                                   "unit_price":q.get("unit_price")})
        p["boq"]=build_boq(boq_inputs)
        self.store.save(project_id,p); return row


    def recalculate_estimate(self, project_id: str, *, factors: dict[str,float] | None = None) -> dict[str,Any]:
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        estimate=build_estimate(p.get("boq",[]), factors=factors or {}, aggregate=False)
        p["estimate"]=estimate
        self.store.save(project_id,p)
        return estimate

    def build_commercial_snapshot(self, project_id: str, *, factors: dict[str,float] | None = None) -> dict[str,Any]:
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        estimate=self.recalculate_estimate(project_id,factors=factors)
        p=self.store.get(project_id) or p
        lines=[]
        for row in p.get("boq",[]):
            lines.append({
                "code":row.get("price_code",""),
                "contract_quantity":row.get("quantity",0),
                "previous_quantity":row.get("previous_quantity",0),
                "current_quantity":row.get("current_quantity",0),
                "unit_price":row.get("unit_price",0),
            })
        progress=build_progress(lines) if lines else {"lines":[],"contract_total":0,"current_total":0,"payable_current":0,"balance_current":0}
        return {"project_id":project_id,"estimate":estimate,"progress":progress,
                "boq_summary":boq_summary(p.get("boq",[]))}

    def validate(self,project_id:str): 
        p=self.store.get(project_id); return self.qa.run(p or {})

    def report(self,project_id:str,fmt:str,path):
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        rows=[]
        for t in p.get("takeoffs",[]):
            for q in t.get("quantities",[]): rows.append({"کد":q.get("code",""),"شرح":q.get("title",""),
                "مقدار":q.get("amount",0),"واحد":q.get("unit",""),"فرمول":q.get("formula","")})
        return build_report(p.get("name",""),rows,{"grand_total":sum(float(x["مقدار"]) for x in rows)}).export(path,fmt)
