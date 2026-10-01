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
        normalized_factors={str(k):float(v) for k,v in (factors or {}).items()}
        estimate=build_estimate(p.get("boq",[]), factors=normalized_factors, aggregate=False)
        # Keep the application service deterministic even if a downstream costing adapter is replaced.
        if normalized_factors:
            base=float(estimate["cost"].get("base",0) or 0)
            subtotal=base
            applied={}
            for name,rate in normalized_factors.items():
                delta=subtotal*rate
                applied[name]=delta
                subtotal+=delta
            estimate["cost"]["factors"]=applied
            estimate["cost"]["grand_total"]=subtotal
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

    def build_statement(self, project_id: str, *, previous_paid: float = 0.0,
                        retention_rate: float = 0.0, advance_recovery_rate: float = 0.0,
                        tax_rate: float = 0.0, insurance_rate: float = 0.0) -> dict[str, Any]:
        """Build a period payment statement directly from the project's BOQ."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        if min(previous_paid, retention_rate, advance_recovery_rate, tax_rate, insurance_rate) < 0:
            raise ValueError("statement rates and previous payment cannot be negative")
        lines = []
        for row in p.get("boq", []):
            lines.append({
                "code": row.get("price_code", ""),
                "description": row.get("description", ""),
                "unit": row.get("unit", ""),
                "contract_quantity": row.get("quantity", 0),
                "unit_price": row.get("unit_price", 0),
                "previous_quantity": row.get("previous_quantity", 0),
                "current_quantity": row.get("current_quantity", 0),
            })
        progress = build_progress(lines) if lines else {
            "lines": [], "contract_total": 0, "completed_total": 0, "current_total": 0,
            "gross_current": 0, "deductions": 0, "payable_current": 0,
            "payments": 0, "balance_current": 0, "remaining_contract": 0, "progress_percent": 0,
        }
        gross = float(progress.get("gross_current", 0) or 0)
        retention = gross * float(retention_rate)
        advance = gross * float(advance_recovery_rate)
        taxable = max(gross - retention - advance, 0.0)
        tax = taxable * float(tax_rate)
        insurance = taxable * float(insurance_rate)
        payable = max(taxable + tax - insurance, 0.0)
        return {
            **progress,
            "retention": retention,
            "advance_recovery": advance,
            "taxable_current": taxable,
            "tax": tax,
            "insurance": insurance,
            "payable_current": payable,
            "previous_paid": float(previous_paid),
            "balance_after_current": payable - float(previous_paid),
            "rates": {
                "retention_rate": float(retention_rate),
                "advance_recovery_rate": float(advance_recovery_rate),
                "tax_rate": float(tax_rate),
                "insurance_rate": float(insurance_rate),
            },
        }

    def save_statement_period(self, project_id: str, *, period_no: int | None = None,
                              current_quantities: dict[str, float] | None = None,
                              retention_rate: float = 0.0, advance_recovery_rate: float = 0.0,
                              tax_rate: float = 0.0, insurance_rate: float = 0.0) -> dict[str, Any]:
        """Persist a numbered statement period and roll its quantities into the next period."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        periods = list(p.get("statement_periods", []))
        if period_no is None:
            period_no = (max((int(x.get("number", 0)) for x in periods), default=0) + 1)
        period_no = int(period_no)
        if period_no <= 0 or any(int(x.get("number", 0)) == period_no for x in periods):
            raise ValueError("statement period number must be positive and unique")
        previous = {}
        if periods:
            previous = {
                str(x.get("code", "")): float(x.get("cumulative_quantity", 0) or 0)
                for x in periods[-1].get("lines", [])
            }
        overrides = {str(k): float(v) for k, v in (current_quantities or {}).items()}
        lines = []
        for row in p.get("boq", []):
            code = str(row.get("price_code", "") or "")
            cur = float(overrides.get(code, row.get("current_quantity", 0)) or 0)
            prev = float(previous.get(code, row.get("previous_quantity", 0)) or 0)
            if cur < 0 or prev < 0:
                raise ValueError("statement quantities cannot be negative")
            lines.append({
                "code": code, "description": row.get("description", ""), "unit": row.get("unit", ""),
                "contract_quantity": float(row.get("quantity", 0) or 0),
                "unit_price": float(row.get("unit_price", 0) or 0),
                "previous_quantity": prev, "current_quantity": cur,
            })
        progress = build_progress(lines)
        period = {
            "number": period_no,
            "lines": progress["lines"],
            "gross_current": progress["gross_current"],
            "completed_total": progress["completed_total"],
            "remaining_contract": progress["remaining_contract"],
            "progress_percent": progress["progress_percent"],
            "rates": {
                "retention_rate": float(retention_rate), "advance_recovery_rate": float(advance_recovery_rate),
                "tax_rate": float(tax_rate), "insurance_rate": float(insurance_rate),
            },
        }
        gross = float(period["gross_current"])
        retention = gross * float(retention_rate)
        advance = gross * float(advance_recovery_rate)
        taxable = max(gross - retention - advance, 0.0)
        tax = taxable * float(tax_rate)
        insurance = taxable * float(insurance_rate)
        period.update({
            "retention": retention, "advance_recovery": advance, "taxable_current": taxable,
            "tax": tax, "insurance": insurance, "payable_current": max(taxable + tax - insurance, 0.0),
        })
        periods.append(period)
        p["statement_periods"] = periods
        self.store.save(project_id, p)
        return period

    def statement_periods(self, project_id: str) -> list[dict[str, Any]]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        return list(p.get("statement_periods", []))

    def validate(self,project_id:str): 
        p=self.store.get(project_id); return self.qa.run(p or {})

    def report(self,project_id:str,fmt:str,path):
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        estimate=p.get("estimate") or build_estimate(p.get("boq",[]), aggregate=False)
        statement=self.build_statement(project_id)
        rows=[]
        for row in statement.get("lines",[]):
            rows.append({"کد":row.get("code",""),"شرح":row.get("description",""),
                "واحد":row.get("unit",""),"مقدار قرارداد":row.get("contract_quantity",0),
                "قبلی":row.get("previous_quantity",0),"این دوره":row.get("current_quantity",0),
                "تجمعی":row.get("cumulative_quantity",0),"قیمت واحد":row.get("unit_price",0),
                "مبلغ این دوره":row.get("current_amount",0),"مبلغ تجمعی":row.get("completed_amount",0)})
        summary={**estimate.get("cost",{}), "statement": {
            "gross_current":statement.get("gross_current",0),
            "retention":statement.get("retention",0),
            "advance_recovery":statement.get("advance_recovery",0),
            "taxable_current":statement.get("taxable_current",0),
            "tax":statement.get("tax",0),
            "insurance":statement.get("insurance",0),
            "payable_current":statement.get("payable_current",0),
            "previous_paid":statement.get("previous_paid",0),
            "balance_after_current":statement.get("balance_after_current",0),
        }}
        return build_report(p.get("name",""),rows,summary).export(path,fmt)
