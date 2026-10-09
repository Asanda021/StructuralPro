"""Project-linked Persian manual takeoff dialog for StructuralPro."""
from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QHeaderView,
)

from core.takeoff.manual_input import parse_manual_batch
from core.takeoff.manual_workbench import ManualTakeoffDraft, ManualTakeoffWorkbench

_ENGINE_CODES = {
    "column": ("building", "column"),
    "beam": ("building", "beam"),
    "tie_beam": ("building", "tie_beam"),
    "footing_concrete": ("advanced", "footing_concrete"),
    "shear_wall": ("building", "shear_wall"),
    "solid_slab_roof": ("building", "solid_slab_roof"),
    "joist_block_roof": ("building", "joist_block_roof"),
    "joist_foam_roof": ("building", "joist_foam_roof"),
    "stair_concrete": ("building", "stair_concrete"),
    "wall": ("building", "wall"),
    "excavation": ("civil", "excavation"),
    "rebar": ("building", "rebar"),
    "steel": ("advanced", "steel"),
}


class ManualTakeoffDialog(QDialog):
    """Collect explicit manual entries, preview quantities, then persist to the active project."""

    def __init__(self, service, project_id: str = "", parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("متره دستی حرفه‌ای — پروژه‌محور")
        self.resize(1080, 720)
        self.project_id = QLineEdit(project_id)
        self.floor_id = QLineEdit("طبقه همکف")
        self.element_label = QLineEdit()
        self.entry_text = QTextEdit()
        self.entry_text.setPlaceholderText(
            "نمونه: ستون: تعداد=12، عرض=0.5، عمق=0.5، ارتفاع=3\n"
            "هر ردیف جداگانه یا با ; وارد شود. واحد ابعاد متر است."
        )
        self.status = QLabel("ورودی کامل محاسبه می‌شود؛ ورودی ناقص ذخیره نخواهد شد.")
        self.status.setWordWrap(True)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["شناسه", "طبقه", "نوع", "شرح", "مقدار", "واحد", "وضعیت"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.workbench = None
        self._saved_ids: set[str] = set()

        root = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("شناسه پروژه:", self.project_id)
        form.addRow("طبقه / تراز:", self.floor_id)
        form.addRow("شرح عضو (اختیاری):", self.element_label)
        root.addLayout(form)
        root.addWidget(QLabel("ورودی متره"))
        root.addWidget(self.entry_text, 2)
        actions = QHBoxLayout()
        self.add_button = QPushButton("محاسبه و افزودن به پیش‌نمایش")
        self.save_button = QPushButton("ذخیره ردیف‌های محاسبه‌شده در پروژه")
        self.close_button = QPushButton("بستن")
        actions.addWidget(self.add_button)
        actions.addWidget(self.save_button)
        actions.addWidget(self.close_button)
        root.addLayout(actions)
        root.addWidget(self.table, 3)
        root.addWidget(self.status)
        self.add_button.clicked.connect(self.add_entries)
        self.save_button.clicked.connect(self.save_pending)
        self.close_button.clicked.connect(self.accept)

    def add_entries(self):
        project_id = self.project_id.text().strip()
        floor_id = self.floor_id.text().strip()
        if not project_id:
            QMessageBox.warning(self, "شناسه پروژه", "ابتدا شناسه پروژه را وارد کن.")
            return
        if not floor_id:
            QMessageBox.warning(self, "طبقه", "طبقه یا تراز را مشخص کن.")
            return
        project = self.service.open_project(project_id)
        if project is None:
            QMessageBox.warning(self, "پروژه", "این پروژه وجود ندارد؛ ابتدا آن را در بخش پروژه‌ها ایجاد کن.")
            return
        if self.workbench is None or self.workbench.project_id != project_id:
            self.workbench = ManualTakeoffWorkbench(project_id)
            self._saved_ids.clear()
            self.table.setRowCount(0)
        try:
            entries = parse_manual_batch(self.entry_text.toPlainText())
        except Exception as exc:
            QMessageBox.warning(self, "ورودی متره", str(exc))
            return

        label = self.element_label.text().strip()
        results = []
        row_errors = []
        for entry in entries:
            try:
                results.append(
                    self.workbench.add_text(
                        entry.source_text, floor_id=floor_id, element_label=label
                    )
                )
            except Exception as exc:
                row_errors.append(f"{entry.source_text}: {exc}")

        added = 0
        incomplete = []
        for result in results:
            row = self.table.rowCount()
            self.table.insertRow(row)
            if isinstance(result, ManualTakeoffDraft):
                values = [
                    "پیش‌نویس", result.floor_id, result.entry.code,
                    self.element_label.text().strip() or result.entry.code,
                    "—", "—", "نیازمند: " + "، ".join(result.missing),
                ]
                incomplete.append(f"{result.entry.code}: {', '.join(result.missing)}")
            else:
                values = [
                    result.record_id, result.floor_id, result.code,
                    result.element_label, f"{result.quantity:g}", result.unit,
                    "آماده ذخیره",
                ]
                added += 1
            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if col == 6:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, cell)
        messages = []
        if incomplete:
            messages.append(f"{len(incomplete)} ردیف ناقص: " + " | ".join(incomplete))
        if row_errors:
            messages.append(f"{len(row_errors)} ردیف خطادار: " + " | ".join(row_errors))
        messages.insert(0, f"{added} ردیف کامل محاسبه شد.")
        self.status.setText(" ".join(messages) + " برای ثبت دائمی، ذخیره ردیف‌ها را بزن.")
        self.entry_text.clear()

    def save_pending(self):
        if self.workbench is None or not self.workbench.records:
            QMessageBox.information(self, "ذخیره متره", "ردیف کامل و محاسبه‌شده‌ای برای ذخیره وجود ندارد.")
            return
        saved = 0
        errors = []
        for record in self.workbench.records:
            if record.record_id in self._saved_ids:
                continue
            mapping = _ENGINE_CODES.get(record.code)
            if mapping is None:
                errors.append(f"{record.record_id}: نوع آیتم پشتیبانی نمی‌شود.")
                continue
            domain, item = mapping
            try:
                self.service.add_takeoff(
                    record.project_id,
                    domain,
                    item,
                    description=record.element_label,
                    source_id=f"manual-workbench:{uuid4().hex}",
                    system=record.floor_id,
                    **dict(record.params),
                )
                self._saved_ids.add(record.record_id)
                saved += 1
                for row in range(self.table.rowCount()):
                    id_cell = self.table.item(row, 0)
                    if id_cell and id_cell.text() == record.record_id:
                        self.table.setItem(row, 6, QTableWidgetItem("ذخیره شد"))
                        break
            except Exception as exc:
                errors.append(f"{record.record_id}: {exc}")
        if saved:
            self.status.setText(f"{saved} ردیف در پروژه ذخیره شد." + ((" خطاها: " + " | ".join(errors)) if errors else ""))
        elif errors:
            self.status.setText("هیچ ردیفی ذخیره نشد: " + " | ".join(errors))
        else:
            self.status.setText("همه ردیف‌های کامل قبلاً ذخیره شده‌اند.")
