"""Report exporters with structured commercial summaries and RTL-aware tables."""
from __future__ import annotations
from pathlib import Path


def _summary_items(summary):
    summary = summary or {}
    cost = summary.get("cost", summary)
    items = []
    labels = (
        ("base", "مبلغ پایه"),
        ("grand_total", "مبلغ نهایی"),
        ("line_count", "تعداد ردیف"),
    )
    for key, label in labels:
        if key in cost:
            items.append((label, cost.get(key)))
    factors = cost.get("factors", {}) if isinstance(cost, dict) else {}
    for name, value in factors.items():
        items.append((str(name), value))
    statement = summary.get("statement", {}) if isinstance(summary, dict) else {}
    statement_labels = (
        ("gross_current", "مبلغ ناخالص این دوره"),
        ("retention", "کسور تضمین"),
        ("advance_recovery", "استهلاک پیش‌پرداخت"),
        ("taxable_current", "مبلغ مشمول مالیات"),
        ("tax", "مالیات"),
        ("insurance", "بیمه"),
        ("payable_current", "قابل پرداخت این دوره"),
        ("previous_paid", "پرداختی قبلی"),
        ("balance_after_current", "مانده پس از این دوره"),
    )
    for key, label in statement_labels:
        if key in statement:
            items.append((label, statement.get(key)))
    if "period_no" in summary:
        items.insert(0, ("شماره صورت‌وضعیت", summary["period_no"]))
    return items


def export_csv(rows, path, title="StructuralPro", summary=None):
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


def export_xlsx(rows, path, title="StructuralPro", summary=None):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = (title or "Report")[:31]
    ws.sheet_view.rightToLeft = True
    ws.append([title])
    ws.append(["خلاصه تجاری"])
    for label, value in _summary_items(summary):
        ws.append([label, value])
    ws.append([])
    keys = list(rows[0].keys()) if rows else []
    if keys:
        ws.append(keys)
        for row in rows:
            ws.append([row.get(k, "") for k in keys])
    header_row = 7 if _summary_items(summary) else 4
    if not keys:
        header_row = ws.max_row
    ws.freeze_panes = f"A{header_row + 1}"
    if keys:
        ws.auto_filter.ref = f"A{header_row}:{chr(64 + min(len(keys), 26))}{ws.max_row}"
        for cell in ws[header_row]:
            cell.font = Font(bold=True)
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                horizontal="right", readingOrder=2, vertical="top", wrap_text=True
            )
    ws.column_dimensions["A"].width = max(18, min(42, max((len(str(c.value or "")) for c in ws["A"]), default=18) + 2))
    for column in range(2, min(ws.max_column, 12) + 1):
        ws.column_dimensions[chr(64 + column)].width = 18
    wb.save(path)
    return path


def export_docx(rows, path, title="StructuralPro", summary=None):
    from docx import Document
    from docx.enum.table import WD_TABLE_DIRECTION
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    d = Document()
    d.add_heading(title, 0)
    d.add_heading("خلاصه تجاری", level=1)
    summary_table = d.add_table(rows=0, cols=2)
    try:
        summary_table.direction = WD_TABLE_DIRECTION.RTL
    except Exception:
        pass
    for label, value in _summary_items(summary):
        cells = summary_table.add_row().cells
        cells[0].text = str(label)
        cells[1].text = str(value)
    d.add_heading("ریز مقادیر و برآورد", level=1)
    keys = list(rows[0].keys()) if rows else ["StructuralPro"]
    t = d.add_table(rows=1, cols=len(keys))
    try:
        t.direction = WD_TABLE_DIRECTION.RTL
    except Exception:
        pass
    for i, k in enumerate(keys):
        t.rows[0].cells[i].text = str(k)
    for row in rows:
        cells = t.add_row().cells
        for i, k in enumerate(keys):
            cells[i].text = str(row.get(k, ""))
    d.save(path)
    return path


def export_pdf(rows, path, title="StructuralPro", summary=None):
    from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys()) if rows else ["StructuralPro"]
    data = [keys] + [[str(row.get(k, "")) for k in keys] for row in rows]
    styles = getSampleStyleSheet()
    rtl = ParagraphStyle("rtl", parent=styles["BodyText"], alignment=TA_RIGHT, fontName="Helvetica")
    doc = SimpleDocTemplate(
        str(path), pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24
    )
    story = [Paragraph(title, styles["Title"]), Spacer(1, 10), Paragraph("خلاصه تجاری", styles["Heading2"])]
    summary_rows = _summary_items(summary)
    if summary_rows:
        story.append(Table([["شرح", "مقدار"]] + [[str(a), str(b)] for a, b in summary_rows], repeatRows=1))
        story.append(Spacer(1, 12))
    story.append(Paragraph("ریز مقادیر و برآورد", styles["Heading2"]))
    story.append(Table(data, repeatRows=1))
    doc.build(story)
    return path
