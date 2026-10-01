"""Professional deterministic report model and export contract."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable


DEFAULT_COLUMNS = (
    ("item_no", "ردیف"),
    ("item_code", "کد آیتم"),
    ("price_code", "کد قیمت"),
    ("chapter", "فصل"),
    ("category", "دسته"),
    ("group", "گروه"),
    ("description", "شرح"),
    ("quantity", "مقدار"),
    ("unit", "واحد"),
    ("unit_price", "بهای واحد"),
    ("total", "مبلغ"),
    ("status", "وضعیت"),
    ("source_id", "منبع متره"),
    ("notes", "یادداشت"),
)


def normalize_report_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for index, row in enumerate(rows, 1):
        item = dict(row)
        item.setdefault("item_no", index)
        result.append(item)
    return result


def report_columns(rows: Iterable[dict[str, Any]]) -> list[tuple[str, str]]:
    rows = list(rows)
    present = {key for row in rows for key in row}
    columns = [(key, label) for key, label in DEFAULT_COLUMNS if key in present]
    extras = sorted(present - {key for key, _ in DEFAULT_COLUMNS})
    columns.extend((key, key.replace("_", " ")) for key in extras)
    return columns


@dataclass
class ProjectReport:
    project_name: str
    rows: list[dict[str, Any]]
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.rows = normalize_report_rows(self.rows)
        self.summary = dict(self.summary or {})
        self.metadata = dict(self.metadata or {})

    def as_rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]

    def columns(self) -> list[tuple[str, str]]:
        return report_columns(self.rows)

    def validate(self) -> dict[str, Any]:
        errors = []
        if not str(self.project_name or "").strip():
            errors.append("missing_project_name")
        for index, row in enumerate(self.rows, 1):
            if not str(row.get("description") or "").strip():
                errors.append(f"row_{index}:missing_description")
        return {"valid": not errors, "errors": errors, "line_count": len(self.rows)}

    def export(self, path, fmt):
        from .exporters import export_csv, export_xlsx, export_docx, export_pdf
        f = str(fmt).lower().lstrip(".")
        exporters = {"csv": export_csv, "xlsx": export_xlsx, "docx": export_docx, "pdf": export_pdf}
        if f not in exporters:
            raise ValueError(f"unsupported report format: {fmt}")
        return exporters[f](
            self.rows, path, title=self.project_name, summary=self.summary,
            metadata=self.metadata, columns=self.columns(),
        )


def build_report(project_name, rows, summary=None, metadata=None):
    return ProjectReport(project_name, list(rows), summary or {}, metadata or {})
