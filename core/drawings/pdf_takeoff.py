from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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

class PDFTakeoffAdapter:
    """Offline PDF inspection; graphical measurement can be injected later."""
    def inspect(self, path: str | Path) -> list[PDFPageInfo]:
        p = Path(path)
        if not p.exists(): raise FileNotFoundError(p)
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF inspection") from exc
        reader = PdfReader(str(p)); result=[]
        for i,page in enumerate(reader.pages,1):
            box=page.mediabox
            result.append(PDFPageInfo(i,float(box.width),float(box.height),page.extract_text() or ""))
        return result
    def measurements(self, pages: Iterable[PDFPageInfo]) -> list[Measurement]:
        return []
