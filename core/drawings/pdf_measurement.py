"""Persistent graphical PDF measurement session with calibration and hole subtraction."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable
import math, json

@dataclass(frozen=True)
class Measurement:
    id: str
    page: int
    kind: str
    quantity: float
    unit: str
    points: tuple[tuple[float,float], ...] = ()
    label: str = ""
    source: str = "manual"

class PDFMeasurementSession:
    def __init__(self, scale: float = 1.0, unit: str = "m"):
        if scale <= 0: raise ValueError("scale must be positive")
        self.scale=float(scale); self.unit=unit; self.measurements:list[Measurement]=[]

    def calibrate(self, pixel_distance: float, real_distance: float, real_unit: str="m") -> float:
        if pixel_distance <= 0 or real_distance <= 0: raise ValueError("calibration distances must be positive")
        factor=real_distance/pixel_distance
        if real_unit=="mm": factor/=1000
        elif real_unit=="cm": factor/=100
        elif real_unit!="m": raise ValueError("unsupported real unit")
        self.scale=factor; self.unit="m"; return self.scale

    def add_length(self, page:int, points:Iterable[tuple[float,float]], *, label="", id=None) -> Measurement:
        pts=tuple((float(x),float(y)) for x,y in points)
        if len(pts)<2: raise ValueError("length needs at least two points")
        px=sum(math.dist(pts[i],pts[i+1]) for i in range(len(pts)-1))
        m=Measurement(id or f"m{len(self.measurements)+1}",int(page),"length",px*self.scale,"m",pts,label)
        self.measurements.append(m); return m

    def add_area(self, page:int, points:Iterable[tuple[float,float]], *, holes=(), label="", id=None) -> Measurement:
        pts=tuple((float(x),float(y)) for x,y in points)
        if len(pts)<3: raise ValueError("area needs at least three points")
        def poly(ps):
            return abs(sum(ps[i][0]*ps[(i+1)%len(ps)][1]-ps[(i+1)%len(ps)][0]*ps[i][1] for i in range(len(ps)))/2)
        area=poly(pts)*self.scale*self.scale
        for hole in holes:
            hp=tuple((float(x),float(y)) for x,y in hole)
            if len(hp)>=3: area-=poly(hp)*self.scale*self.scale
        if area < -1e-9: raise ValueError("holes exceed polygon area")
        m=Measurement(id or f"m{len(self.measurements)+1}",int(page),"area",max(0.0,area),"m2",pts,label)
        self.measurements.append(m); return m

    def add_count(self,page:int,count:int=1,*,label="",id=None)->Measurement:
        if count < 0: raise ValueError("count cannot be negative")
        m=Measurement(id or f"m{len(self.measurements)+1}",int(page),"count",float(count),"عدد",(),label)
        self.measurements.append(m); return m

    def remove(self, measurement_id:str)->bool:
        old=len(self.measurements); self.measurements=[m for m in self.measurements if m.id!=measurement_id]
        return len(self.measurements)!=old

    def by_page(self,page:int): return [m for m in self.measurements if m.page==int(page)]

    def to_dict(self): return {"scale":self.scale,"unit":self.unit,"measurements":[asdict(m) for m in self.measurements]}

    def to_json(self): return json.dumps(self.to_dict(),ensure_ascii=False)

    @classmethod
    def from_dict(cls,data):
        s=cls(float(data.get("scale",1)),data.get("unit","m"))
        for raw in data.get("measurements",[]):
            s.measurements.append(Measurement(raw["id"],int(raw["page"]),raw["kind"],float(raw["quantity"]),raw["unit"],tuple(tuple(p) for p in raw.get("points",())),raw.get("label",""),raw.get("source","manual")))
        return s
