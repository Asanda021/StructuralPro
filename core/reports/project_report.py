"""Unified project report builder."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .exporters import export_csv, export_xlsx, export_docx, export_pdf

@dataclass
class ProjectReport:
    project_name: str
    rows: list[dict[str, Any]]
    summary: dict[str, Any]
    def as_rows(self):
        return self.rows
    def export(self, path, fmt):
        f = fmt.lower().lstrip(".")
        exporters = {
            "csv": export_csv, "xlsx": export_xlsx,
            "docx": export_docx, "pdf": export_pdf,
        }
        if f not in exporters:
            raise ValueError(f"unsupported report format: {fmt}")
        return exporters[f](self.rows, path, title=self.project_name)

def build_report(project_name, rows, summary=None):
    return ProjectReport(project_name, list(rows), summary or {})
