"""Contract and item model for offline project commercial control."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Iterable
@dataclass(frozen=True)
class ContractItem:
    code:str; description:str; unit:str; quantity:float; unit_price:float
    @property
    def amount(self): return float(self.quantity)*float(self.unit_price)
@dataclass
class Contract:
    contract_id:str; title:str; items:list[ContractItem]; advance_paid:float=0.0
    overhead_rate:float=0.0; regional_rate:float=0.0; retention_rate:float=0.0
    def validate(self)->list[str]:
        e=[]
        if not self.contract_id.strip(): e.append("missing_contract_id")
        for i,x in enumerate(self.items,1):
            if x.quantity<0 or x.unit_price<0: e.append(f"item_{i}_negative_value")
            if not x.code.strip(): e.append(f"item_{i}_missing_code")
        for n,r in (("overhead_rate",self.overhead_rate),("regional_rate",self.regional_rate),("retention_rate",self.retention_rate)):
            if not 0<=float(r)<=1: e.append(f"{n}_out_of_range")
        if self.advance_paid<0: e.append("negative_advance")
        return e
    def total(self): return sum(x.amount for x in self.items)
    def to_dict(self): return {**asdict(self),"items":[asdict(x) for x in self.items],"total":self.total()}
