"""Report exporters with RTL-aware, portable output."""
from __future__ import annotations
from pathlib import Path

def export_csv(rows,path,title="StructuralPro"):
    import csv
    rows=list(rows); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(rows[0].keys()) if rows else []
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
    return path

def export_xlsx(rows,path,title="StructuralPro"):
    from openpyxl import Workbook
    from openpyxl.styles import Font,Alignment
    rows=list(rows); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    wb=Workbook(); ws=wb.active; ws.title=(title or "Report")[:31]
    keys=list(rows[0].keys()) if rows else []
    ws.append(keys)
    for row in rows: ws.append([row.get(k,"") for k in keys])
    ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
    for cell in ws[1]:
        cell.font=Font(bold=True); cell.alignment=Alignment(horizontal="right",readingOrder=2)
    for row in ws.iter_rows():
        for cell in row: cell.alignment=Alignment(horizontal="right",readingOrder=2,vertical="top",wrap_text=True)
    wb.save(path); return path

def export_docx(rows,path,title="StructuralPro"):
    from docx import Document
    from docx.enum.table import WD_TABLE_DIRECTION
    rows=list(rows); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    d=Document(); d.add_heading(title,0)
    keys=list(rows[0].keys()) if rows else []
    t=d.add_table(rows=1,cols=len(keys))
    try: t.direction=WD_TABLE_DIRECTION.RTL
    except Exception: pass
    for i,k in enumerate(keys): t.rows[0].cells[i].text=str(k)
    for row in rows:
        cells=t.add_row().cells
        for i,k in enumerate(keys): cells[i].text=str(row.get(k,""))
    d.save(path); return path

def export_pdf(rows,path,title="StructuralPro"):
    from reportlab.platypus import SimpleDocTemplate,Table,Paragraph
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    rows=list(rows); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(rows[0].keys()) if rows else ["StructuralPro"]
    data=[keys]+[[str(row.get(k,"")) for k in keys] for row in rows]
    styles=getSampleStyleSheet()
    style=ParagraphStyle("rtl",parent=styles["BodyText"],alignment=2,fontName="Helvetica")
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=24,leftMargin=24,topMargin=24,bottomMargin=24)
    doc.build([Paragraph(title,styles["Title"]),Table(data,repeatRows=1)])
    return path
