"""Higher-level offline AI assistant combining deterministic QA and local LLM responses."""
from __future__ import annotations
from core.ai.local_engine import LocalAIEngine
from core.ai.takeoff_assistant import LocalTakeoffAssistant

class ProjectAssistant:
    def __init__(self):
        self.engine=LocalAIEngine()
        self.takeoff=LocalTakeoffAssistant()

    def review(self, project:dict) -> dict:
        response=self.engine.inspect_project(project)
        issues=self.takeoff.qa([
            {"quantity":q.get("amount"),"unit":q.get("unit"),"price_code":q.get("price_code")}
            for t in project.get("takeoffs",[]) for q in t.get("quantities",[])
        ])
        return {"text":response.text,"source":response.source,"confidence":response.confidence,
                "issues":issues,"offline":True}

    def compare_rows(self, old:list[dict], new:list[dict]) -> list[dict]:
        def key(r): return str(r.get("price_code") or r.get("description") or "")
        a={key(x):x for x in old}; b={key(x):x for x in new}
        out=[]
        for k in sorted(set(a)|set(b)):
            oq=float(a.get(k,{}).get("quantity",0) or 0); nq=float(b.get(k,{}).get("quantity",0) or 0)
            if oq!=nq: out.append({"key":k,"old":oq,"new":nq,"delta":nq-oq})
        return out
