"""Deterministic building/architectural quantity operations.

All operations are unit-aware and intentionally independent from pricing.
They accept normalized dictionaries so the same engine can be driven by
forms, CAD rules, BIM quantities, or imported schedules.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class QuantityResult:
    category: str
    item: str
    quantity: float
    unit: str
    formula: str
    warnings: tuple[str, ...] = ()

def _n(v: Any, name: str, *, minimum: float = 0.0) -> float:
    try: x=float(v)
    except (TypeError, ValueError): raise ValueError(f"{name} must be numeric")
    if x < minimum: raise ValueError(f"{name} must be >= {minimum}")
    return x

def _rect_area(length,width): return _n(length,"length")*_n(width,"width")
def _wall_area(length,height,openings=0): return max(0.0,_n(length,"length")*_n(height,"height")-_n(openings,"openings"))

def calculate_building_item(item: str, **p: Any) -> QuantityResult:
    k=item.strip().casefold().replace(" ","_")
    if k in {"wall","wall_area","دیوار"}:
        q=_wall_area(p["length"],p["height"],p.get("openings",0)); return QuantityResult("ابنیه","دیوار",q,"m2","L×H−بازشو")
    if k in {"slab","slab_area","floor","کف"}:
        q=_rect_area(p["length"],p["width"]); return QuantityResult("ابنیه","سطح سقف/کف",q,"m2","L×W")
    if k in {"slab_volume","concrete_slab","بتن_سقف"}:
        q=_rect_area(p["length"],p["width"])*_n(p["thickness"],"thickness")*_n(p.get("count",1),"count"); return QuantityResult("ابنیه","بتن سقف",q,"m3","L×W×t×تعداد")
    if k in {"tie_beam","tie_beam_concrete","شناژ"}:
        q=_rect_area(p["width"],p["depth"])*_n(p["length"],"length")*_n(p.get("count",1),"count"); return QuantityResult("سازه","شناژ / کلاف بتنی",q,"m3","b×h×L×تعداد")
    if k in {"shear_wall","shear_wall_concrete","دیوار_برشی"}:
        q=_n(p["length"],"length")*_n(p["thickness"],"thickness")*_n(p["height"],"height")*_n(p.get("count",1),"count"); return QuantityResult("سازه","دیوار برشی بتنی",q,"m3","L×t×H×تعداد")
    if k in {"stair_concrete","stair","پله_بتنی"}:
        q=_rect_area(p["length"],p["width"])*_n(p["thickness"],"thickness")*_n(p.get("count",1),"count"); return QuantityResult("سازه","حجم مدل پایه پله بتنی",q,"m3","L×W×t×تعداد")
    if k in {"roof_area","roof","سقف"}:
        q=_rect_area(p["length"],p["width"])*_n(p.get("count",1),"count"); return QuantityResult("سقف","مساحت سیستم سقف",q,"m2","L×W×تعداد")
    if k in {"column","column_concrete","بتن_ستون"}:
        q=_rect_area(p["width"],p["depth"])*_n(p["height"],"height")*_n(p.get("count",1),"count"); return QuantityResult("سازه","بتن ستون",q,"m3","b×h×H×تعداد")
    if k in {"beam","beam_concrete","بتن_تیر"}:
        q=_rect_area(p["width"],p["depth"])*_n(p["length"],"length")*_n(p.get("count",1),"count"); return QuantityResult("سازه","بتن تیر",q,"m3","b×h×L×تعداد")
    if k in {"formwork","formwork_area","قالب"}:
        q=_n(p["perimeter"],"perimeter")*_n(p["height"],"height")*_n(p.get("count",1),"count"); return QuantityResult("بتن","قالب‌بندی",q,"m2","محیط×ارتفاع×تعداد")
    if k in {"plaster","plaster_area","گچ","گچ_کاری","paint","paint_area","رنگ"}:
        q=_wall_area(p["length"],p["height"],p.get("openings",0))*_n(p.get("count",1),"count"); return QuantityResult("نازک‌کاری",item,q,"m2","سطح خالص×تعداد")
    if k in {"tile","ceramic","tile_area","کاشی","سرامیک"}:
        q=_wall_area(p["length"],p["height"],p.get("openings",0))*_n(p.get("waste",1.0),"waste",minimum=0); return QuantityResult("نازک‌کاری",item,q,"m2","سطح خالص×ضریب پرت")
    if k in {"roof_insulation","waterproofing","عایق"}:
        q=_rect_area(p["length"],p["width"])*_n(p.get("layers",1),"layers"); return QuantityResult("عایق‌کاری",item,q,"m2","L×W×لایه")
    if k in {"door","window","opening","درب","پنجره"}:
        q=_n(p.get("count",1),"count"); return QuantityResult("در و پنجره",item,q,"عدد","تعداد")
    if k in {"rebar","reinforcement","آرماتور"}:
        q=_n(p["length"],"length")*_n(p["unit_weight"],"unit_weight")*_n(p.get("count",1),"count"); return QuantityResult("آرماتور",item,q,"kg","L×وزن واحد×تعداد")
    raise KeyError(f"unsupported building item: {item}")
