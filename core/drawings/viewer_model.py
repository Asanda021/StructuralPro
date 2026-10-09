"""Transactional drawing viewer model for PDF/DXF/DWG sources."""
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
        return DrawingViewport(min(self.left, self.left + self.width),
                               min(self.top, self.top + self.height),
                               abs(self.width), abs(self.height))


class DrawingViewerModel:
    """Load a real drawing; failed imports never replace the currently open drawing."""

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
            raise FileNotFoundError(f"فایل نقشه پیدا نشد یا فایل معمولی نیست: {p}")
        ext = p.suffix.lower()
        new_kind = ""
        new_page_count = 0
        new_cad_document = None
        if ext == ".pdf":
            from core.drawings.pdf_engine import PDFDrawingEngine
            # Close the underlying PDF handle after validating the file and page count.
            with PDFDrawingEngine(p) as engine:
                new_kind = "pdf"
                new_page_count = engine.page_count
                if new_page_count < 1:
                    raise ValueError("PDF هیچ صفحه قابل‌نمایشی ندارد.")
        elif ext in {".dwg", ".dxf"}:
            from core.drawings.dwg_takeoff import DWGTakeoffEngine
            new_cad_document = DWGTakeoffEngine().import_file(p)
            new_kind = "cad"
            new_page_count = 1
        else:
            raise ValueError("فرمت نقشه باید PDF، DWG یا DXF باشد.")

        # Commit viewer state only after the complete import/validation succeeds.
        self.path = p
        self.kind = new_kind
        self.page_count = new_page_count
        self.cad_document = new_cad_document
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
        return {"pages": self.page_count, "source": str(self.path or ""), "kind": self.kind}

    def clamp_page(self, page: int) -> int:
        try:
            value = int(page)
        except (TypeError, ValueError) as exc:
            raise ValueError("شماره صفحه باید عدد صحیح باشد.") from exc
        return max(1, min(value, max(1, self.page_count)))
