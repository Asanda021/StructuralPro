"""Professional PDF drawing session: page rendering, zoom metadata and snap-ready geometry.
PyMuPDF is optional; deterministic measurement remains available without rendering.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import math

@dataclass(frozen=True)
class PDFPage:
    number:int
    width_pt:float
    height_pt:float
    rotation:int=0

@dataclass(frozen=True)
class SnapPoint:
    x:float
    y:float
    source:str="manual"

class PDFDrawingEngine:
    def __init__(self,path:str|Path):
        self.path=Path(path)
        if not self.path.exists(): raise FileNotFoundError(self.path)
        self._doc=None
    def open(self):
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for PDF graphical viewing") from exc
        if self._doc is None: self._doc=fitz.open(str(self.path))
        return self
    @property
    def page_count(self):
        self.open(); return len(self._doc)
    def pages(self)->list[PDFPage]:
        self.open()
        return [PDFPage(i+1,float(p.rect.width),float(p.rect.height),int(p.rotation)) for i,p in enumerate(self._doc)]
    def render(self,page:int,dpi:int=120)->bytes:
        self.open()
        if not 1 <= page <= len(self._doc): raise IndexError(page)
        if dpi<36 or dpi>600: raise ValueError("dpi must be between 36 and 600")
        p=self._doc[page-1]
        pix=p.get_pixmap(dpi=dpi,alpha=False)
        return pix.tobytes("png")
    def text(self,page:int)->str:
        self.open()
        return self._doc[page-1].get_text("text") or ""
    @staticmethod
    def snap(point:tuple[float,float],candidates:Iterable[SnapPoint],tolerance:float=8.0):
        if tolerance<0: raise ValueError("tolerance cannot be negative")
        pts=list(candidates)
        if not pts: return point
        x,y=point; best=min(pts,key=lambda p:math.hypot(p.x-x,p.y-y))
        return (best.x,best.y) if math.hypot(best.x-x,best.y-y)<=tolerance else point
