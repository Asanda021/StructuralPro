"""Unified drawing viewer model for PDF/DXF/DWG sources.

The viewer model deliberately keeps rendering concerns out of the deterministic
takeoff engine. PDF pages use the real PDF renderer; CAD uses the existing
DWG/DXF parser and preserves layer/entity provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DrawingViewport:
    left: float
    top: float
    width: float
    height: float

    def normalized(self) -> "DrawingViewport":
        return DrawingViewport(
            min(self.left, self.left + self.width),
            min(self.top, self.top + self.height),
            abs(self.width),
            abs(self.height),
        )


class DrawingViewerModel:
    """Load a drawing and expose deterministic page/CAD information."""

    def __init__(self, path: str | Path | None = None):
        self.path: Path | None = None
        self.kind: str = ""
        self.page_count = 0
        self.cad_document: Any = None
        self.current_page = 1
        if path:
            self.open(path)

    def open(self, path: str | Path) -> "DrawingViewerModel":
        p = Path(path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"فایل نقشه پیدا نشد: {p}")
        ext = p.suffix.lower()
        self.path = p
        self.cad_document = None
        if ext == ".pdf":
            from core.drawings.pdf_engine import PDFDrawingEngine
            engine = PDFDrawingEngine(p)
            self.kind = "pdf"
            self.page_count = int(engine.page_count)
        elif ext in {".dwg", ".dxf"}:
            from core.drawings.dwg_takeoff import DWGTakeoffEngine
            self.cad_document = DWGTakeoffEngine().import_file(p)
            self.kind = "cad"
            self.page_count = 1
        else:
            raise ValueError("فرمت نقشه باید PDF، DWG یا DXF باشد.")
        self.current_page = 1
        return self

    @property
    def source_name(self) -> str:
        return self.path.name if self.path else ""

    @property
    def summary(self) -> dict[str, Any]:
        if self.kind == "cad" and self.cad_document is not None:
            from core.drawings.dwg_takeoff import DWGTakeoffEngine
            return DWGTakeoffEngine().summarize(self.cad_document)
        return {"pages": self.page_count, "source": str(self.path or "")}

    def clamp_page(self, page: int) -> int:
        return max(1, min(int(page), max(1, self.page_count)))
