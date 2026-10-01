"""Application service shared by desktop and future mobile/chat clients."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from core.projects.store import ProjectStore
from core.takeoff.engine import TakeoffEngine
from core.takeoff.boq import build_boq
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
             "formula":result.formula,"warning":result.warning}]}
        p["takeoffs"].append(row)
        p["boq"]=build_boq([{"source":"manual","description":item,"quantity":result.quantity,"unit":result.unit,
                             "price_code":params.get("price_code"),"unit_price":params.get("unit_price")}])
        self.store.save(project_id,p); return row

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
