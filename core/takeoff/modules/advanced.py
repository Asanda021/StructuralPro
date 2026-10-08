"""Extended construction quantity operations used by the unified takeoff engine."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

def _n(v: Any, name: str, minimum: float = 0.0) -> float:
    try: x=float(v)
    except (TypeError, ValueError): raise ValueError(f"{name} must be numeric")
    if x < minimum: raise ValueError(f"{name} must be >= {minimum}")
    return x

@dataclass(frozen=True)
class AdvancedQuantity:
    category: str
    item: str
    quantity: float
    unit: str
    formula: str

def calculate_advanced_item(item: str, **p: Any) -> AdvancedQuantity:
    k=item.strip().casefold().replace(" ","_")
    if k in {"excavation","خاکبرداری"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p["depth"],"depth")*_n(p.get("count",1),"count")
        return AdvancedQuantity("خاکی","خاکبرداری",q,"m3","L×W×D×تعداد")
    if k in {"demolition","demolition_volume","تخریب"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p["height"],"height")*_n(p.get("count",1),"count")
        return AdvancedQuantity("تخریب","تخریب حجمی",q,"m3","L×W×H×تعداد")
    if k in {"footing_concrete","foundation_concrete","بتن_فونداسیون"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p["thickness"],"thickness")*_n(p.get("count",1),"count")
        return AdvancedQuantity("فونداسیون","بتن فونداسیون",q,"m3","L×W×t×تعداد")
    if k in {"footing_formwork","قالب_فونداسیون"}:
        q=_n(p["perimeter"],"perimeter")*_n(p["height"],"height")*_n(p.get("count",1),"count")
        return AdvancedQuantity("فونداسیون","قالب فونداسیون",q,"m2","محیط×ارتفاع×تعداد")
    if k in {"steel","steel_roof","steel_weight","اسکلت_فلزی"}:
        q=_n(p["length"],"length")*_n(p["unit_weight"],"unit_weight")*_n(p.get("count",1),"count")
        return AdvancedQuantity("اسکلت فلزی","وزن فولاد",q,"kg","L×وزن واحد×تعداد")
    if k in {"screed","کف_سازی"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p["thickness"],"thickness")*_n(p.get("count",1),"count")
        return AdvancedQuantity("کف‌سازی","حجم کف‌سازی",q,"m3","L×W×t×تعداد")
    if k in {"facade","نما"}:
        q=max(0.0,_n(p["length"],"length")*_n(p["height"],"height")-_n(p.get("openings",0),"openings"))
        return AdvancedQuantity("نما","سطح نما",q,"m2","L×H−بازشو")
    if k in {"ceiling","false_ceiling","سقف_کاذب"}:
        q=_n(p["length"],"length")*_n(p["width"],"width")*_n(p.get("count",1),"count")
        return AdvancedQuantity("سقف کاذب","سطح سقف کاذب",q,"m2","L×W×تعداد")
    raise KeyError(f"unsupported advanced item: {item}")
