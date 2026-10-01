"""Year-aware commercial factor sets; factors are explicit, auditable and composable."""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class FactorSet:
    year:int
    name:str
    factors:dict[str,float]
    source:str=""
    effective_date:str=""
    notes:str=""

class FactorRegistry:
    def __init__(self,sets=()):
        self._sets={(int(x.year),x.name):x for x in sets}
    def add(self,x:FactorSet):
        if x.year<1300: raise ValueError("invalid year")
        if any(float(v)<-1 for v in x.factors.values()): raise ValueError("factor rate is invalid")
        self._sets[(x.year,x.name)]=x
    def years(self): return sorted({y for y,_ in self._sets},reverse=True)
    def names(self,year): return sorted(n for y,n in self._sets if y==int(year))
    def get(self,year,name): return self._sets.get((int(year),name))
    def rates(self,year,name):
        x=self.get(year,name)
        if x is None: raise KeyError((year,name))
        return dict(x.factors)
    def describe(self,year,name):
        x=self.get(year,name)
        return None if x is None else asdict(x)
