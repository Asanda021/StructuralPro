"""Commercial payment statement with cumulative quantities and transparent deductions."""
from __future__ import annotations
from typing import Iterable
from core.projects.statement_engine import StatementLine,build_statement

def build_payment_statement(contract, current:Iterable[StatementLine], *, previous_paid=0.0, advance_recovery_rate=0.0, other_deduction_rate=0.0):
    errors=contract.validate()
    if errors: raise ValueError("; ".join(errors))
    result=build_statement(current,retention_rate=contract.retention_rate,
        advance_recovery_rate=advance_recovery_rate,other_deduction_rate=other_deduction_rate,
        advance_paid=contract.advance_paid)
    gross=float(result["gross_current"])
    result["contract_id"]=contract.contract_id
    result["contract_total"]=contract.total()
    result["commercial_base_current"]=gross
    result["commercial_total_current"]=contract.commercial_total(gross)
    result["tax"] = contract.tax_rate * result["commercial_total_current"]
    result["insurance"] = contract.insurance_rate * result["commercial_total_current"]
    result["previous_paid"]=float(previous_paid)
    result["balance_after_current"]=contract.commercial_total()-float(previous_paid)-result["payable"]
    result["commercial_factors"]={"overhead_rate":contract.overhead_rate,"regional_rate":contract.regional_rate,
        "retention_rate":contract.retention_rate,"tax_rate":contract.tax_rate,"insurance_rate":contract.insurance_rate}
    return result

class PaymentStatement:
    def __init__(self,contract): self.contract=contract
    def build(self,lines,**kwargs): return build_payment_statement(self.contract,lines,**kwargs)
