"""Offline PDF inspection and text/dimension-assisted takeoff primitives."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import re

@dataclass(frozen=True)
class PDFPageInfo:
    page: int
    width: float | None
    height: float | None
    text: str

@dataclass(frozen=True)
class Measurement:
    kind: str
    value: float
    unit: str
    source: str
    page: int | None = None
    label: str = ""

_DIM_RE = re.compile(r"(?P<label>[A-Za-zآ-ی0-9_\- ]{0,40})?\s*(?P<value>\d+(?:[\.,]\d+)?)\s*(?P<unit>mm|cm|m|متر|سانت|میلی?متر)?", re.I)

class PDFTakeoffAdapter:
    def inspect(self, path: str | Path) -> list[PDFPageInfo]:
        p=Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF inspection") from exc
        reader=PdfReader(str(p)); result=[]
        for i,page in enumerate(reader.pages,1):
            box=page.mediabox
            result.append(PDFPageInfo(i,float(box.width),float(box.height),page.extract_text() or ""))
        return result

    def measurements(self, pages: Iterable[PDFPageInfo]) -> list[Measurement]:
        out=[]
        for page in pages:
            for m in _DIM_RE.finditer(page.text):
                value=float(m.group("value").replace(",","."))
                unit=(m.group("unit") or "").lower()
                if not unit: continue
                if unit in ("mm","میلیمتر"): value/=1000; unit="m"
                elif unit in ("cm","سانت"): value/=100; unit="m"
                elif unit in ("متر","m"): unit="m"
                out.append(Measurement("dimension",value,unit,"pdf-text",page.page,(m.group("label") or "").strip()))
        return out

    def text_takeoff_candidates(self, pages: Iterable[PDFPageInfo]) -> list[dict]:
        rows=[]
        for m in self.measurements(pages):
            rows.append({"source":f"pdf:p{m.page}","description":m.label or "dimension",
                         "quantity":m.value,"unit":m.unit,"confidence":0.45,
                         "needs_confirmation":True})
        return rows
