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


def _normalize_date_key(value: str) -> str | None:
    """Normalize simple Persian/Gregorian project dates for deterministic aging checks."""
    raw = str(value or "").strip()
    if not raw:
        return None
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    raw = raw.translate(trans).replace("-", "/").replace(".", "/")
    parts = raw.split("/")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        return None
    y, m, d = (int(part) for part in parts)
    if y < 1 or not 1 <= m <= 12 or not 1 <= d <= 31:
        return None
    return f"{y:04d}/{m:02d}/{d:02d}"

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

    def add_project_financial_document(self, project_id: str, document_number: str, document_type: str, amount: float, *, counterparty: str = "", date: str = "", due_date: str = "", reference: str = "", notes: str = "", payment_status: str = "unpaid", commitment_id: int | None = None, cost_entry_id: int | None = None, receipt_id: int | None = None) -> dict[str, Any]:
        """Persist a project financial invoice/document and optionally link it to a ledger entry."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        document_number = str(document_number).strip()
        document_type = str(document_type).strip()
        payment_status = str(payment_status).strip().lower()
        amount = float(amount)
        if not document_number:
            raise ValueError("document number cannot be empty")
        if not document_type:
            raise ValueError("document type cannot be empty")
        if amount < 0:
            raise ValueError("document amount cannot be negative")
        if payment_status not in {"unpaid", "partial", "paid"}:
            raise ValueError("invalid payment status")
        documents = list(p.get("financial_documents", []))
        if any(str(x.get("document_number", "")) == document_number for x in documents):
            raise ValueError("document number must be unique within the project")
        def _exists(collection: str, entry_id: int | None) -> bool:
            return entry_id is None or any(int(x.get("id", 0)) == int(entry_id) for x in p.get(collection, []))
        if not _exists("commitment_entries", commitment_id):
            raise KeyError(f"commitment {commitment_id}")
        if not _exists("cost_entries", cost_entry_id):
            raise KeyError(f"cost entry {cost_entry_id}")
        if not _exists("receipt_entries", receipt_id):
            raise KeyError(f"receipt {receipt_id}")
        entry = {
            "id": len(documents) + 1,
            "document_number": document_number,
            "document_type": document_type,
            "counterparty": str(counterparty).strip(),
            "amount": amount,
            "date": str(date).strip(),
            "due_date": str(due_date).strip(),
            "reference": str(reference).strip(),
            "notes": str(notes).strip(),
            "payment_status": payment_status,
            "commitment_id": int(commitment_id) if commitment_id is not None else None,
            "cost_entry_id": int(cost_entry_id) if cost_entry_id is not None else None,
            "receipt_id": int(receipt_id) if receipt_id is not None else None,
        }
        documents.append(entry)
        p["financial_documents"] = documents
        self.store.save(project_id, p)
        return entry

    def project_financial_documents(self, project_id: str) -> list[dict[str, Any]]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        return list(p.get("financial_documents", []))

    def project_financial_document_summary(self, project_id: str) -> dict[str, Any]:
        entries = self.project_financial_documents(project_id)
        by_status = {"unpaid": 0.0, "partial": 0.0, "paid": 0.0}
        by_type: dict[str, float] = {}
        for entry in entries:
            amount = float(entry.get("amount", 0) or 0)
            status = str(entry.get("payment_status", "unpaid"))
            by_status[status] = by_status.get(status, 0.0) + amount
            dtype = str(entry.get("document_type", "سایر"))
            by_type[dtype] = by_type.get(dtype, 0.0) + amount
        return {
            "project_id": project_id,
            "document_count": len(entries),
            "document_total": sum(float(x.get("amount", 0) or 0) for x in entries),
            "by_payment_status": by_status,
            "by_type": by_type,
        }

    def add_project_cost(self, project_id: str, category: str, amount: float, *, description: str = "", date: str = "", document_id: int | None = None, counterparty: str = "") -> dict[str, Any]:
        """Persist an actual project cost entry for financial control."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        amount = float(amount)
        if amount < 0:
            raise ValueError("cost amount cannot be negative")
        categories = {"مصالح", "دستمزد", "پیمانکار", "تجهیزات", "سایر"}
        category = str(category).strip()
        if category not in categories:
            raise ValueError(f"unsupported cost category: {category}")
        if document_id is not None and not any(int(x.get("id", 0)) == int(document_id) for x in p.get("financial_documents", [])):
            raise KeyError(f"financial document {document_id}")
        entries = list(p.get("cost_entries", []))
        entry = {
            "id": len(entries) + 1,
            "category": category,
            "amount": amount,
            "description": str(description).strip(),
            "date": str(date).strip(),
            "counterparty": str(counterparty).strip(),
            "document_id": int(document_id) if document_id is not None else None,
        }
        entries.append(entry)
        p["cost_entries"] = entries
        self.store.save(project_id, p)
        return entry

    def project_costs(self, project_id: str) -> list[dict[str, Any]]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        return list(p.get("cost_entries", []))

    def project_cost_summary(self, project_id: str) -> dict[str, Any]:
        entries = self.project_costs(project_id)
        by_category = {}
        for entry in entries:
            category = str(entry.get("category", "سایر"))
            by_category[category] = by_category.get(category, 0.0) + float(entry.get("amount", 0) or 0)
        return {
            "project_id": project_id,
            "entry_count": len(entries),
            "actual_cost": sum(by_category.values()),
            "by_category": by_category,
        }

    def project_financial_control(self, project_id: str, *, planned_cost: float | None = None,
                                  actual_cost: float = 0.0) -> dict[str, Any]:
        """Calculate cost variance indicators from explicit project cost inputs."""
        if actual_cost < 0 or (planned_cost is not None and planned_cost < 0):
            raise ValueError("cost values cannot be negative")
        dashboard = self.financial_dashboard(project_id)
        contract = float(dashboard["contract_amount"])
        work = float(dashboard["cumulative_work"])
        planned = contract if planned_cost is None else float(planned_cost)
        ledger_actual = float(self.project_cost_summary(project_id)["actual_cost"])
        actual = ledger_actual if actual_cost == 0 else float(actual_cost)
        earned = work
        cost_variance = earned - actual
        schedule_variance = earned - (planned * dashboard["progress_percent"] / 100.0 if planned else 0.0)
        cost_ratio = (earned / actual) if actual > 0 else None
        budget_ratio = (earned / planned) if planned > 0 else None
        return {
            "project_id": project_id,
            "contract_amount": contract,
            "planned_cost": planned,
            "actual_cost": actual,
            "earned_value": earned,
            "cost_variance": cost_variance,
            "schedule_variance": schedule_variance,
            "cost_performance_index": cost_ratio,
            "budget_progress_ratio": budget_ratio,
            "progress_percent": dashboard["progress_percent"],
        }

    def financial_dashboard(self, project_id: str) -> dict[str, Any]:
        """Return a compact financial/progress snapshot for the project dashboard."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        estimate = p.get("estimate") or self.recalculate_estimate(project_id)
        cost = estimate.get("cost", {}) or {}
        boq = p.get("boq", []) or []
        contract = float(cost.get("grand_total", 0) or 0)
        base = float(cost.get("base", 0) or 0)
        snapshot = self.build_commercial_snapshot(project_id)
        progress = snapshot.get("progress", {}) or {}
        periods = list(p.get("statement_periods", []))
        latest = periods[-1] if periods else None
        cumulative = float(progress.get("completed_total", 0) or 0)
        if latest is not None:
            cumulative = float(latest.get("completed_total", cumulative) or cumulative)
        remaining = max(contract - cumulative, 0.0)
        percent = (cumulative / contract * 100.0) if contract else 0.0
        total_payable = sum(float(x.get("payable_current", 0) or 0) for x in periods)
        cost_summary = self.project_cost_summary(project_id)
        actual_cost = float(cost_summary["actual_cost"])
        gross_margin = cumulative - actual_cost
        return {
            "project_id": project_id,
            "project_name": p.get("name", ""),
            "line_count": len(boq),
            "contract_amount": contract,
            "base_amount": base,
            "cumulative_work": cumulative,
            "remaining_contract": remaining,
            "progress_percent": percent,
            "statement_count": len(periods),
            "latest_statement_no": latest.get("number") if latest else None,
            "latest_payable": float(latest.get("payable_current", 0) or 0) if latest else 0.0,
            "total_payable": total_payable,
            "actual_cost": actual_cost,
            "gross_margin": gross_margin,
            "cost_entry_count": cost_summary["entry_count"],
            "cost_by_category": cost_summary["by_category"],
            "warnings": list((estimate.get("warnings") or [])),
        }

    def validate(self,project_id:str): 
        p=self.store.get(project_id); return self.qa.run(p or {})

    def add_project_commitment(self, project_id: str, amount: float, *, category: str = "سایر", description: str = "", date: str = "", due_date: str = "", reference: str = "", paid_amount: float = 0.0, document_id: int | None = None, counterparty: str = "") -> dict[str, Any]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        amount = float(amount)
        paid_amount = float(paid_amount)
        if amount < 0 or paid_amount < 0 or paid_amount > amount:
            raise ValueError("invalid commitment amount")
        if document_id is not None and not any(int(x.get("id", 0)) == int(document_id) for x in p.get("financial_documents", [])):
            raise KeyError(f"financial document {document_id}")
        entries = list(p.get("commitment_entries", []))
        entry = {"id": len(entries) + 1, "amount": amount, "paid_amount": paid_amount, "category": str(category).strip() or "سایر", "description": str(description).strip(), "date": str(date).strip(), "due_date": str(due_date).strip(), "reference": str(reference).strip(), "document_id": int(document_id) if document_id is not None else None, "counterparty": str(counterparty).strip()}
        entries.append(entry)
        p["commitment_entries"] = entries
        self.store.save(project_id, p)
        return entry

    def project_commitments(self, project_id: str) -> list[dict[str, Any]]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        return list(p.get("commitment_entries", []))

    def project_commitment_summary(self, project_id: str) -> dict[str, Any]:
        entries = self.project_commitments(project_id)
        total = sum(float(x.get("amount", 0) or 0) for x in entries)
        paid = sum(float(x.get("paid_amount", 0) or 0) for x in entries)
        return {"project_id": project_id, "entry_count": len(entries), "committed_total": total, "paid_total": paid, "unpaid_total": max(total - paid, 0.0)}

    def add_project_receipt(self, project_id: str, amount: float, *, description: str = "", date: str = "", reference: str = "", document_id: int | None = None, counterparty: str = "") -> dict[str, Any]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        amount = float(amount)
        if amount < 0:
            raise ValueError("receipt amount cannot be negative")
        if document_id is not None and not any(int(x.get("id", 0)) == int(document_id) for x in p.get("financial_documents", [])):
            raise KeyError(f"financial document {document_id}")
        entries = list(p.get("receipt_entries", []))
        entry = {"id": len(entries) + 1, "amount": amount, "description": str(description).strip(), "date": str(date).strip(), "reference": str(reference).strip(), "document_id": int(document_id) if document_id is not None else None, "counterparty": str(counterparty).strip()}
        entries.append(entry)
        p["receipt_entries"] = entries
        self.store.save(project_id, p)
        return entry

    def project_receipts(self, project_id: str) -> list[dict[str, Any]]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        return list(p.get("receipt_entries", []))

    def project_receipt_summary(self, project_id: str) -> dict[str, Any]:
        entries = self.project_receipts(project_id)
        return {"project_id": project_id, "entry_count": len(entries), "total_received": sum(float(x.get("amount", 0) or 0) for x in entries)}

    def project_financial_position(self, project_id: str) -> dict[str, Any]:
        dashboard = self.financial_dashboard(project_id)
        receipts = self.project_receipt_summary(project_id)
        commitments = self.project_commitment_summary(project_id)
        contract = float(dashboard["contract_amount"])
        received = float(receipts["total_received"])
        receivable = max(contract - received, 0.0)
        committed = float(commitments["committed_total"])
        return {
            "project_id": project_id, "contract_amount": contract,
            "earned_value": float(dashboard["cumulative_work"]), "actual_cost": float(dashboard["actual_cost"]),
            "received": received, "receivable": receivable,
            "committed_cost": committed, "unpaid_commitments": float(commitments["unpaid_total"]),
            "cash_exposure": max(committed - received, 0.0),
            "cost_margin": float(dashboard["gross_margin"]), "receipt_count": receipts["entry_count"],
            "commitment_count": commitments["entry_count"],
        }

    def project_cost_report(self, project_id: str, fmt: str, path):
        """Export the project's persisted cost ledger with category totals."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        entries = self.project_costs(project_id)
        summary = self.project_cost_summary(project_id)
        rows = [{
            "ردیف": entry.get("id", ""),
            "دسته": entry.get("category", ""),
            "شرح": entry.get("description", ""),
            "تاریخ": entry.get("date", ""),
            "مبلغ": float(entry.get("amount", 0) or 0),
        } for entry in entries]
        by_category = summary["by_category"]
        summary_payload = {
            "receipts": self.project_receipt_summary(project_id),
            "financial_position": self.project_financial_position(project_id),
            "cost": {
                "line_count": summary["entry_count"],
                "grand_total": summary["actual_cost"],
                "base": summary["actual_cost"],
                "factors": by_category,
            }
        }
        return build_report(f'{p.get("name", "")} — گزارش هزینه پروژه', rows, summary_payload).export(path, fmt)

    def add_project_counterparty(self, project_id: str, name: str, *, role: str = "", notes: str = "") -> dict[str, Any]:
        """Create a normalized project counterparty master record."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        name = " ".join(str(name).strip().split())
        role = " ".join(str(role).strip().split())
        if not name:
            raise ValueError("counterparty name cannot be empty")
        records = list(p.get("counterparties", []))
        key = name.casefold()
        if any(str(x.get("name", "")).strip().casefold() == key for x in records):
            raise ValueError("counterparty already exists")
        record = {
            "id": f"CP{len(records)+1:04d}",
            "name": name,
            "role": role,
            "notes": str(notes).strip(),
        }
        records.append(record)
        p["counterparties"] = records
        self.store.save(project_id, p)
        return record

    def project_counterparties(self, project_id: str) -> list[dict[str, Any]]:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        return list(p.get("counterparties", []))

    def find_project_counterparty(self, project_id: str, name: str) -> dict[str, Any] | None:
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        key = " ".join(str(name).strip().split()).casefold()
        if not key:
            return None
        return next((x for x in p.get("counterparties", []) if str(x.get("name", "")).casefold() == key), None)


    def project_counterparty_summary(self, project_id: str) -> dict[str, Any]:
        """Aggregate project financial exposure by counterparty."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        result: dict[str, dict[str, Any]] = {}
        def bucket(name: str) -> dict[str, Any]:
            key = str(name or "").strip() or "نامشخص"
            return result.setdefault(key, {"counterparty": key, "documents": 0, "document_amount": 0.0,
                                           "commitments": 0, "committed_amount": 0.0, "paid_commitments": 0.0,
                                           "cost_entries": 0, "actual_cost": 0.0, "receipts": 0, "received": 0.0})
        for d in p.get("financial_documents", []):
            b = bucket(d.get("counterparty", ""))
            b["documents"] += 1
            b["document_amount"] += float(d.get("amount", 0) or 0)
        for c in p.get("commitment_entries", []):
            # Commitment records predate counterparty support; use their optional field when available.
            b = bucket(c.get("counterparty", ""))
            b["commitments"] += 1
            b["committed_amount"] += float(c.get("amount", 0) or 0)
            b["paid_commitments"] += float(c.get("paid_amount", 0) or 0)
        for c in p.get("cost_entries", []):
            b = bucket(c.get("counterparty", ""))
            b["cost_entries"] += 1
            b["actual_cost"] += float(c.get("amount", 0) or 0)
        for r in p.get("receipt_entries", []):
            b = bucket(r.get("counterparty", ""))
            b["receipts"] += 1
            b["received"] += float(r.get("amount", 0) or 0)
        for b in result.values():
            b["unpaid_commitments"] = max(b["committed_amount"] - b["paid_commitments"], 0.0)
            b["net_cash"] = b["received"] - b["paid_commitments"]
        return {"project_id": project_id, "counterparties": list(result.values()),
                "counterparty_count": len(result)}

    def project_counterparty_ledger(self, project_id: str, counterparty: str) -> dict[str, Any]:
        """Return chronological financial activity for one project counterparty."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        name = str(counterparty).strip()
        if not name:
            raise ValueError("counterparty cannot be empty")
        rows = []
        def add(source: str, entry: dict[str, Any], amount: float, direction: str):
            rows.append({
                "source": source, "id": entry.get("id", ""), "date": entry.get("date", ""),
                "reference": entry.get("reference", ""), "description": entry.get("description", ""),
                "amount": float(amount), "direction": direction,
                "cash_in": float(amount) if direction == "in" else 0.0,
                "cash_out": float(amount) if direction == "out" else 0.0,
                "document_id": entry.get("document_id"),
            })
        for entry in p.get("financial_documents", []):
            if str(entry.get("counterparty", "")).strip() == name:
                add("سند مالی", entry, entry.get("amount", 0), "info")
        for entry in p.get("commitment_entries", []):
            if str(entry.get("counterparty", "")).strip() == name:
                add("تعهد", entry, entry.get("amount", 0), "out")
        for entry in p.get("cost_entries", []):
            if str(entry.get("counterparty", "")).strip() == name:
                add("هزینه", entry, entry.get("amount", 0), "out")
        for entry in p.get("receipt_entries", []):
            if str(entry.get("counterparty", "")).strip() == name:
                add("دریافتی", entry, entry.get("amount", 0), "in")
        rows.sort(key=lambda x: (str(x.get("date", "")), str(x.get("source", "")), int(x.get("id", 0) or 0)))
        cash_in = sum(x["cash_in"] for x in rows)
        cash_out = sum(x["cash_out"] for x in rows)
        return {
            "project_id": project_id, "counterparty": name, "rows": rows,
            "row_count": len(rows), "cash_in": cash_in, "cash_out": cash_out,
            "net_cash": cash_in - cash_out,
        }

    def project_counterparty_ledger_report(self, project_id: str, counterparty: str, fmt: str, path):
        """Export a detailed counterparty transaction ledger."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        ledger = self.project_counterparty_ledger(project_id, counterparty)
        rows = [{
            "نوع": x["source"], "شناسه": x["id"], "تاریخ": x["date"], "مرجع": x["reference"],
            "شرح": x["description"], "مبلغ": x["amount"], "جهت": x["direction"],
            "دریافت": x["cash_in"], "پرداخت": x["cash_out"], "سند مالی": x["document_id"] or "",
        } for x in ledger["rows"]]
        return build_report(f'{p.get("name", "")} — گردش حساب {counterparty}', rows, ledger).export(path, fmt)

    def project_counterparty_report(self, project_id: str, fmt: str, path):
        """Export the counterparty financial ledger."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        summary = self.project_counterparty_summary(project_id)
        rows = []
        for b in summary["counterparties"]:
            rows.append({
                "طرف حساب": b["counterparty"], "اسناد": b["documents"], "مبلغ اسناد": b["document_amount"],
                "تعهدات": b["commitments"], "مبلغ تعهدات": b["committed_amount"],
                "پرداخت تعهدات": b["paid_commitments"], "پرداخت‌نشده": b["unpaid_commitments"],
                "هزینه واقعی": b["actual_cost"], "دریافتی": b["received"], "خالص نقدی": b["net_cash"],
            })
        return build_report(f'{p.get("name", "")} — گردش مالی طرف حساب‌ها', rows, summary).export(path, fmt)

    def project_financial_aging(self, project_id: str, as_of: str) -> dict[str, Any]:
        """Return deterministic due-date aging for unpaid project financial items.

        The caller supplies the reporting date explicitly. This avoids mixing the
        project's Jalali date strings with the machine's Gregorian clock.
        """
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        as_of_key = _normalize_date_key(as_of)
        if as_of_key is None:
            raise ValueError("invalid aging date; expected YYYY/MM/DD")
        rows = []

        def classify(due_date: str) -> str:
            due_key = _normalize_date_key(due_date)
            if due_key is None:
                return "بدون سررسید"
            if due_key < as_of_key:
                return "معوق"
            if due_key == as_of_key:
                return "سررسید امروز"
            return "آتی"

        for entry in p.get("commitment_entries", []):
            amount = float(entry.get("amount", 0) or 0)
            paid = float(entry.get("paid_amount", 0) or 0)
            outstanding = max(amount - paid, 0.0)
            if outstanding <= 0:
                continue
            due_date = str(entry.get("due_date", "")).strip()
            status = classify(due_date)
            rows.append({
                "source": "تعهد", "id": entry.get("id", ""), "counterparty": entry.get("counterparty", ""),
                "reference": entry.get("reference", ""), "due_date": due_date, "status": status,
                "amount": amount, "paid_amount": paid, "outstanding": outstanding,
            })

        for entry in p.get("financial_documents", []):
            payment_status = str(entry.get("payment_status", "unpaid")).strip().lower()
            if payment_status == "paid":
                continue
            amount = float(entry.get("amount", 0) or 0)
            due_date = str(entry.get("due_date", "")).strip()
            status = classify(due_date)
            rows.append({
                "source": "سند مالی", "id": entry.get("id", ""), "counterparty": entry.get("counterparty", ""),
                "reference": entry.get("document_number", ""), "due_date": due_date, "status": status,
                "amount": amount, "paid_amount": None, "outstanding": amount if payment_status == "unpaid" else None,
            })

        order = {"معوق": 0, "سررسید امروز": 1, "آتی": 2, "بدون سررسید": 3}
        rows.sort(key=lambda x: (order.get(x["status"], 9), _normalize_date_key(x["due_date"]) or "9999/99/99",
                                str(x["source"]), int(x.get("id", 0) or 0)))
        overdue_commitments = sum(x["outstanding"] for x in rows if x["source"] == "تعهد" and x["status"] == "معوق")
        overdue_unpaid_documents = sum(x["outstanding"] or 0 for x in rows if x["source"] == "سند مالی" and x["status"] == "معوق")
        return {
            "project_id": project_id,
            "as_of": as_of_key,
            "rows": rows,
            "row_count": len(rows),
            "overdue_count": sum(1 for x in rows if x["status"] == "معوق"),
            "due_today_count": sum(1 for x in rows if x["status"] == "سررسید امروز"),
            "upcoming_count": sum(1 for x in rows if x["status"] == "آتی"),
            "no_due_date_count": sum(1 for x in rows if x["status"] == "بدون سررسید"),
            "overdue_commitments": overdue_commitments,
            "overdue_unpaid_documents": overdue_unpaid_documents,
            "overdue_amount": overdue_commitments + overdue_unpaid_documents,
        }

    def project_financial_aging_report(self, project_id: str, as_of: str, fmt: str, path):
        """Export the project's due-date aging center."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        aging = self.project_financial_aging(project_id, as_of)
        rows = [{
            "نوع": x["source"], "شناسه": x["id"], "طرف حساب": x["counterparty"],
            "مرجع": x["reference"], "سررسید": x["due_date"], "وضعیت": x["status"],
            "مبلغ": x["amount"], "پرداخت": x["paid_amount"] if x["paid_amount"] is not None else "",
            "مانده": x["outstanding"] if x["outstanding"] is not None else "",
        } for x in aging["rows"]]
        return build_report(f'{p.get("name", "")} — کنترل سررسید مالی', rows, aging).export(path, fmt)


    def project_financial_report(self, project_id: str, fmt: str, path):
        """Export a consolidated project financial report from all financial ledgers."""
        p = self.store.get(project_id)
        if p is None:
            raise KeyError(project_id)
        position = self.project_financial_position(project_id)
        documents = self.project_financial_documents(project_id)
        costs = self.project_costs(project_id)
        commitments = self.project_commitments(project_id)
        receipts = self.project_receipts(project_id)
        rows = []
        for entry in documents:
            rows.append({
                "نوع": "سند مالی",
                "شناسه": entry.get("id", ""),
                "شماره سند": entry.get("document_number", ""),
                "نوع سند": entry.get("document_type", ""),
                "طرف حساب": entry.get("counterparty", ""),
                "مبلغ": float(entry.get("amount", 0) or 0),
                "تاریخ": entry.get("date", ""),
                "سررسید": entry.get("due_date", ""),
                "وضعیت پرداخت": entry.get("payment_status", ""),
                "تعهد": entry.get("commitment_id", ""),
                "هزینه": entry.get("cost_entry_id", ""),
                "دریافتی": entry.get("receipt_id", ""),
                "مرجع": entry.get("reference", ""),
            })
        for entry in commitments:
            rows.append({
                "نوع": "تعهد",
                "شناسه": entry.get("id", ""),
                "شماره سند": "",
                "نوع سند": entry.get("category", ""),
                "طرف حساب": "",
                "مبلغ": float(entry.get("amount", 0) or 0),
                "تاریخ": entry.get("date", ""),
                "سررسید": entry.get("due_date", ""),
                "وضعیت پرداخت": "paid" if float(entry.get("paid_amount", 0) or 0) >= float(entry.get("amount", 0) or 0) else "unpaid",
                "تعهد": entry.get("id", ""),
                "هزینه": "",
                "دریافتی": "",
                "مرجع": entry.get("reference", ""),
            })
        for entry in costs:
            rows.append({
                "نوع": "هزینه",
                "شناسه": entry.get("id", ""),
                "شماره سند": "",
                "نوع سند": entry.get("category", ""),
                "طرف حساب": "",
                "مبلغ": float(entry.get("amount", 0) or 0),
                "تاریخ": entry.get("date", ""),
                "سررسید": "",
                "وضعیت پرداخت": "",
                "تعهد": "",
                "هزینه": entry.get("id", ""),
                "دریافتی": "",
                "مرجع": "",
            })
        for entry in receipts:
            rows.append({
                "نوع": "دریافتی",
                "شناسه": entry.get("id", ""),
                "شماره سند": "",
                "نوع سند": "دریافتی",
                "طرف حساب": "",
                "مبلغ": float(entry.get("amount", 0) or 0),
                "تاریخ": entry.get("date", ""),
                "سررسید": "",
                "وضعیت پرداخت": "received",
                "تعهد": "",
                "هزینه": "",
                "دریافتی": entry.get("id", ""),
                "مرجع": entry.get("reference", ""),
            })
        doc_summary = self.project_financial_document_summary(project_id)
        summary = {
            "financial_position": position,
            "documents": doc_summary,
            "cost": self.project_cost_summary(project_id),
            "commitments": self.project_commitment_summary(project_id),
            "receipts": self.project_receipt_summary(project_id),
        }
        return build_report(f'{p.get("name", "")} — گزارش مالی تجمیعی پروژه', rows, summary).export(path, fmt)

    def report(self,project_id:str,fmt:str,path,*,period_no:int|None=None):
        p=self.store.get(project_id)
        if p is None: raise KeyError(project_id)
        estimate=p.get("estimate") or build_estimate(p.get("boq",[]), aggregate=False)
        selected=None
        periods=p.get("statement_periods",[])
        if period_no is not None:
            selected=next((x for x in periods if int(x.get("number",0))==int(period_no)),None)
            if selected is None: raise KeyError(f"statement period {period_no}")
        if selected is None:
            statement=self.build_statement(project_id)
            title=p.get("name","")
        else:
            statement=selected
            title=f'{p.get("name","")} — صورت‌وضعیت دوره {selected.get("number")}'
        rows=[]
        for row in statement.get("lines",[]):
            rows.append({"کد":row.get("code",""),"شرح":row.get("description",""),
                "واحد":row.get("unit",""),"مقدار قرارداد":row.get("contract_quantity",0),
                "قبلی":row.get("previous_quantity",0),"این دوره":row.get("current_quantity",0),
                "تجمعی":row.get("cumulative_quantity",0),"قیمت واحد":row.get("unit_price",0),
                "مبلغ این دوره":row.get("current_amount",0),"مبلغ تجمعی":row.get("completed_amount",0)})
        summary={**estimate.get("cost",{}), "period_no": selected.get("number") if selected else None,
                 "statement": {
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
        return build_report(title,rows,summary).export(path,fmt)
