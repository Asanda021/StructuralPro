"""Construction progress and payment-period calculations."""
from __future__ import annotations
from typing import Iterable, Any

def build_progress(lines:Iterable[Any])->dict[str,Any]:
    rows=[]; contract_total=completed_total=current_total=0.0
    for x in lines:
        d=x if isinstance(x,dict) else vars(x)
        cq=float(d.get("contract_quantity",0) or 0); prev=float(d.get("previous_quantity",0) or 0)
        cur=float(d.get("current_quantity",0) or 0); price=float(d.get("unit_price",0) or 0)
        if cq<0 or prev<0 or cur<0: raise ValueError("quantities cannot be negative")
        cumulative=prev+cur; contract_amount=cq*price; completed_amount=min(cumulative,cq)*price
        current_amount=cur*price
        rows.append({**d,"cumulative_quantity":cumulative,"remaining_quantity":max(cq-cumulative,0),
                     "progress_percent":0 if cq==0 else min(cumulative/cq*100,100),
                     "contract_amount":contract_amount,"current_amount":current_amount})
        contract_total+=contract_amount; completed_total+=completed_amount; current_total+=current_amount
    return {"lines":rows,"contract_total":contract_total,"completed_total":completed_total,
            "current_total":current_total,"progress_percent":0 if contract_total==0 else completed_total/contract_total*100}
