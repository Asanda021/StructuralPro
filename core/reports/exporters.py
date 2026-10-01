"""Report exporters with optional XLSX/PDF/DOCX dependencies."""
from __future__ import annotations
from pathlib import Path
from .formatting import table_html

def export_csv(rows, path, title="StructuralPro"):
    import csv
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    return path

def export_xlsx(rows, path, title="StructuralPro"):
    from openpyxl import Workbook
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); rows = list(rows)
    wb = Workbook(); ws = wb.active; ws.title = title[:31]
    keys = list(rows[0].keys()) if rows else []
    ws.append(keys)
    for r in rows: ws.append([r.get(k, "") for k in keys])
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    for cell in ws[1]: cell.font = cell.font.copy(bold=True)
    wb.save(path); return path

def export_docx(rows, path, title="StructuralPro"):
    from docx import Document
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); rows = list(rows)
    d = Document(); d.add_heading(title, 0)
    keys = list(rows[0].keys()) if rows else []
    t = d.add_table(rows=1, cols=len(keys))
    for i, k in enumerate(keys): t.rows[0].cells[i].text = str(k)
    for r in rows:
        cells = t.add_row().cells
        for i, k in enumerate(keys): cells[i].text = str(r.get(k, ""))
    d.save(path); return path

def export_pdf(rows, path, title="StructuralPro"):
    from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); rows = list(rows)
    keys = list(rows[0].keys()) if rows else ["StructuralPro"]
    data = [keys] + [[str(r.get(k, "")) for k in keys] for r in rows]
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    s = getSampleStyleSheet()
    doc.build([Paragraph(title, s["Title"]), Table(data, repeatRows=1)])
    return path
