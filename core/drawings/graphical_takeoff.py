"""Production-grade, dependency-light graphical takeoff primitives.

The module keeps geometry deterministic and UI-independent. A Windows canvas can
store the returned measurement objects directly, making every quantity auditable.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import hypot
import re
from typing import Iterable

@dataclass(frozen=True)
class ScaleCalibration:
    ratio: float
    drawing_unit: str = "cm"
    model_unit: str = "m"
    label: str = ""
    source: str = "manual"

    @classmethod
    def parse(cls, value: str|float, drawing_unit="cm", model_unit="m"):
        if isinstance(value,(int,float)):
            ratio=float(value)
        else:
            m=re.search(r"1\s*[:/]\s*(\d+(?:\.\d+)?)",str(value))
            if not m: raise ValueError("مقیاس باید مانند 1:100 باشد")
            ratio=float(m.group(1))
        if ratio<=0: raise ValueError("مقیاس باید بزرگ‌تر از صفر باشد")
        return cls(ratio,drawing_unit,model_unit,str(value),"manual")

    def length(self,drawing_distance:float)->float:
        factor={"mm":1/1000,"cm":1/100,"m":1}.get(self.drawing_unit)
        if factor is None: raise ValueError(f"واحد نقشه پشتیبانی نمی‌شود: {self.drawing_unit}")
        return float(drawing_distance)*self.ratio*factor

    def area(self,drawing_area:float)->float:
        return self.length(drawing_area**0.5)**2

@dataclass(frozen=True)
class Point:
    x: float
    y: float

@dataclass(frozen=True)
class GraphicMeasurement:
    id: str
    kind: str
    value: float
    unit: str
    page: int|None = None
    layer: str|None = None
    label: str = ""
    source: str = "manual"
    confidence: float = 1.0
    geometry: tuple = ()
    formula: str = ""
    def to_dict(self): return asdict(self)

def polyline_length(points:Iterable[Point],closed=False)->float:
    pts=list(points)
    total=sum(hypot(pts[i+1].x-pts[i].x,pts[i+1].y-pts[i].y) for i in range(len(pts)-1))
    if closed and len(pts)>2: total+=hypot(pts[0].x-pts[-1].x,pts[0].y-pts[-1].y)
    return total

def polygon_area(points:Iterable[Point])->float:
    pts=list(points)
    if len(pts)<3: return 0.0
    return abs(sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts)))/2)

def subtract_areas(gross:float,holes:Iterable[float])->float:
    value=float(gross)-sum(float(x) for x in holes)
    if value < -1e-9: raise ValueError("مجموع بازشوها از مساحت اصلی بیشتر است")
    return max(0.0,value)

def snap_point(point:Point, candidates:Iterable[Point], tolerance:float)->Point:
    pts=list(candidates)
    if not pts: return point
    best=min(pts,key=lambda p:hypot(p.x-point.x,p.y-point.y))
    return best if hypot(best.x-point.x,best.y-point.y)<=tolerance else point

class MeasurementStore:
    def __init__(self): self._items=[]; self._counter=0
    def add_length(self,points,scale:ScaleCalibration,**meta):
        pts=tuple(points); self._counter+=1
        d=polyline_length(pts); value=scale.length(d)
        return self._add(GraphicMeasurement(f"M{self._counter:05d}","length",value,"m",
            geometry=tuple((p.x,p.y) for p in pts),formula=f"{d:g} × {scale.ratio:g}",**meta))
    def add_area(self,points,scale:ScaleCalibration,holes=(),**meta):
        pts=tuple(points); self._counter+=1
        gross=scale.area(polygon_area(pts)); hs=[scale.area(float(h)) for h in holes]
        value=subtract_areas(gross,hs)
        formula=f"مساحت ناخالص {gross:g} - بازشوها {sum(hs):g}"
        return self._add(GraphicMeasurement(f"M{self._counter:05d}","area",value,"m2",
            geometry=tuple((p.x,p.y) for p in pts),formula=formula,**meta))
    def add_count(self,count:int,**meta):
        if int(count)<0: raise ValueError("تعداد نمی‌تواند منفی باشد")
        self._counter+=1
        return self._add(GraphicMeasurement(f"M{self._counter:05d}","count",float(count),"عدد",**meta))
    def _add(self,item): self._items.append(item); return item
    def all(self): return list(self._items)
    def clear(self): self._items.clear()
    def summary(self):
        out={}
        for x in self._items: out[x.unit]=out.get(x.unit,0)+x.value
        return {"count":len(self._items),"by_unit":out}

def extract_scale_candidates(text:str):
    return [float(x) for x in re.findall(r"1\s*[:/]\s*(\d+(?:\.\d+)?)",text or "")]

