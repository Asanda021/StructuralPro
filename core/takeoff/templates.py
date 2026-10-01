"""Ready-to-use construction takeoff templates."""
from dataclasses import dataclass
@dataclass(frozen=True)
class TakeoffTemplate:
    code:str; name:str; item_type:str; fields:tuple[str,...]; formula:str
DEFAULT_TEMPLATES=(
    TakeoffTemplate("WALL-AREA","دیوار","wall",("length","height","openings"),"length*height-openings"),
    TakeoffTemplate("FLOOR-AREA","کف/سقف","slab",("length","width","openings"),"length*width-openings"),
    TakeoffTemplate("COLUMN-VOL","ستون","column",("length","width","height"),"length*width*height"),
    TakeoffTemplate("BEAM-VOL","تیر","beam",("length","width","height"),"length*width*height"),
    TakeoffTemplate("FOOT-VOL","پی","footing",("length","width","height"),"length*width*height"),
)
class TemplateLibrary:
    def __init__(self,templates=DEFAULT_TEMPLATES): self.items={x.code:x for x in templates}
    def search(self,q=""): 
        q=q.casefold().strip(); return [x for x in self.items.values() if not q or q in x.code.casefold() or q in x.name.casefold()]
    def get(self,code): return self.items[code]
