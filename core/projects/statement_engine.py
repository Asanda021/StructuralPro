"""Offline construction payment-statement engine."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Iterable,Any
@dataclass(frozen=True)
class StatementLine:
    code:str; description:str; unit:str; contract_quantity:float; unit_price:float; current_quantity:float; previous_quantity:float=0.0
    def amount_current(self): return self.current_quantity*self.unit_price
    def amount_cumulative(self): return (self.previous_quantity+self.current_quantity)*self.unit_price
def build_statement(lines:Iterable[StatementLine],*,retention_rate=0.0,advance_recovery_rate=0.0,other_deduction_rate=0.0,advance_paid=0.0)->dict[str,Any]:
    rows=[]; gross_current=gross_cumulative=0.0
    for x in lines:
        cur=x.amount_current(); cum=x.amount_cumulative()
        rows.append({**asdict(x),"current_amount":cur,"cumulative_amount":cum,
                     "remaining_quantity":max(0.0,x.contract_quantity-(x.previous_quantity+x.current_quantity))})
        gross_current+=cur; gross_cumulative+=cum
    retention=gross_current*float(retention_rate)
    advance_recovery=min(gross_current*float(advance_recovery_rate),float(advance_paid))
    other=gross_current*float(other_deduction_rate)
    return {"lines":rows,"gross_current":gross_current,"gross_cumulative":gross_cumulative,
            "retention":retention,"advance_recovery":advance_recovery,"other_deductions":other,
            "payable":gross_current-retention-advance_recovery-other}
