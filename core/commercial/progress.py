"""Complete period progress / payment statement calculations."""
from __future__ import annotations

def build_progress(lines,*,deductions=None,payments=None):
    rows=[]; contract_total=completed_total=current_total=0.0
    for x in lines:
        d=x if isinstance(x,dict) else vars(x)
        cq=float(d.get("contract_quantity",0) or 0); prev=float(d.get("previous_quantity",0) or 0); cur=float(d.get("current_quantity",0) or 0); price=float(d.get("unit_price",0) or 0)
        if min(cq,prev,cur,price)<0: raise ValueError("quantities and prices cannot be negative")
        cumulative=prev+cur; contract_amount=cq*price; completed_amount=min(cumulative,cq)*price; current_amount=min(cur,max(cq-prev,0))*price
        rows.append({**d,"cumulative_quantity":cumulative,"remaining_quantity":max(cq-cumulative,0),"progress_percent":0 if cq==0 else min(cumulative/cq*100,100),
                     "contract_amount":contract_amount,"current_amount":current_amount,"completed_amount":completed_amount,"over_contract_quantity":max(cumulative-cq,0)})
        contract_total+=contract_amount; completed_total+=completed_amount; current_total+=current_amount
    gross=current_total
    deduction_total=sum(float(x) for x in (deductions or []))
    payment_total=sum(float(x) for x in (payments or []))
    if deduction_total<0 or payment_total<0: raise ValueError("deductions/payments cannot be negative")
    payable=max(gross-deduction_total,0)
    return {"lines":rows,"contract_total":contract_total,"completed_total":completed_total,"current_total":current_total,
            "gross_current":gross,"deductions":deduction_total,"payable_current":payable,"payments":payment_total,
            "balance_current":payable-payment_total,"remaining_contract":max(contract_total-completed_total,0),
            "progress_percent":0 if contract_total==0 else completed_total/contract_total*100}
