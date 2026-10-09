"""Project-linked Persian manual takeoff dialog for StructuralPro."""
from __future__ import annotations

from uuid import uuid4
from datetime import datetime, timezone

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QHeaderView, QInputDialog,
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
        self._session_id = uuid4().hex

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
        self.paste_button = QPushButton("چسباندن Excel")
        self.edit_button = QPushButton("ویرایش ردیف انتخابی")
        self.copy_button = QPushButton("کپی ردیف")
        self.floor_copy_button = QPushButton("کپی به طبقه دیگر")
        self.delete_button = QPushButton("حذف ردیف انتخابی")
        self.undo_button = QPushButton("واگرد")
        self.redo_button = QPushButton("تکرار")
        self.save_button = QPushButton("ذخیره ردیف‌های محاسبه‌شده در پروژه")
        self.close_button = QPushButton("بستن")
        for button in (self.add_button, self.paste_button, self.edit_button, self.copy_button,
                       self.floor_copy_button, self.delete_button, self.undo_button,
                       self.redo_button, self.save_button, self.close_button):
            actions.addWidget(button)
        root.addLayout(actions)
        root.addWidget(self.table, 3)
        root.addWidget(self.status)
        self.add_button.clicked.connect(self.add_entries)
        self.paste_button.clicked.connect(self.paste_clipboard)
        self.edit_button.clicked.connect(self.edit_selected)
        self.copy_button.clicked.connect(self.copy_selected)
        self.floor_copy_button.clicked.connect(self.copy_selected_to_floor)
        self.delete_button.clicked.connect(self.delete_selected)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        self.save_button.clicked.connect(self.save_pending)
        self.close_button.clicked.connect(self.accept)

    def _audit(self, event: str, details: dict | None = None):
        """Persist a compact, append-only project audit event when storage is available."""
        project_id = self.project_id.text().strip()
        if not project_id:
            return
        try:
            project = self.service.open_project(project_id)
            if project is None:
                return
            timeline = project.setdefault("_manual_takeoff_audit", [])
            timeline.append({
                "at": datetime.now(timezone.utc).isoformat(),
                "event": str(event),
                "details": dict(details or {}),
            })
            project["_manual_takeoff_audit"] = timeline[-500:]
            self.service.store.save(project_id, project)
        except Exception:
            # Audit failures are visible to the user; they must not silently block takeoff.
            self.status.setText("هشدار: متره انجام شد اما ذخیره تاریخچه ممیزی ناموفق بود.")

    def _render_records(self):
        self.table.setRowCount(0)
        if self.workbench is None:
            return
        for record in self.workbench.records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            status = "ذخیره شد" if record.record_id in self._saved_ids else "آماده ذخیره"
            values = [record.record_id, record.floor_id, record.code, record.element_label,
                      f"{record.quantity:g}", record.unit, status]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def paste_clipboard(self):
        text = QApplication.clipboard().text()
        if not text.strip():
            self.status.setText("کلیپ‌بورد خالی است؛ ابتدا ردیف‌ها را از Excel کپی کن.")
            return
        # Excel commonly copies tab-separated cells; accept one source entry per line.
        lines = []
        for line in text.splitlines():
            clean = line.strip()
            if not clean:
                continue
            if "\t" in clean:
                cells = [x.strip() for x in clean.split("\t")]
                clean = " ".join(x for x in cells if x)
            lines.append(clean)
        self.entry_text.setPlainText("\n".join(lines))
        self.status.setText(f"{len(lines)} ردیف آماده بررسی است. هر ردیف باید متن کامل و معتبر متره باشد؛ سلول‌های عددی پراکنده از Excel به‌صورت خودکار تفسیر نمی‌شوند.")

    def _selected_record(self):
        row = self.table.currentRow()
        if row < 0 or self.workbench is None:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return next((r for r in self.workbench.records if r.record_id == item.text()), None)

    def copy_selected(self):
        record = self._selected_record()
        if record is None:
            self.status.setText("یک ردیف کامل را انتخاب کن.")
            return
        QApplication.clipboard().setText(record.source)
        self.status.setText("متن ورودی ردیف در کلیپ‌بورد کپی شد.")

    def edit_selected(self):
        record = self._selected_record()
        if record is None:
            self.status.setText("برای ویرایش، یک ردیف کامل را انتخاب کن.")
            return
        if record.record_id in self._saved_ids:
            QMessageBox.warning(self, "ویرایش متره", "این ردیف قبلاً در پروژه ذخیره شده؛ برای جلوگیری از مغایرت، ویرایش مستقیم آن غیرفعال است.")
            return
        self.entry_text.setPlainText(record.source)
        self.element_label.setText(record.element_label)
        self.workbench.remove_record(record.record_id)
        self._render_records()
        self._audit("edit_started", {"record_id": record.record_id, "floor": record.floor_id})
        self.status.setText("ردیف به ورودی برگشت؛ اصلاحش کن و دوباره محاسبه کن.")

    def copy_selected_to_floor(self):
        record = self._selected_record()
        if record is None:
            self.status.setText("یک ردیف کامل را انتخاب کن.")
            return
        floor, ok = QInputDialog.getText(self, "کپی طبقه", "طبقه مقصد:", text=record.floor_id)
        if not ok or not floor.strip():
            return
        try:
            result = self.workbench.add_text(record.source, floor_id=floor.strip(), element_label=record.element_label)
            if isinstance(result, ManualTakeoffDraft):
                raise ValueError("کپی به‌صورت پیش‌نویس درآمد؛ رکورد جدید ایجاد نشد.")
            self._render_records()
            self._audit("floor_copy", {"source_id": record.record_id, "new_id": result.record_id, "floor": floor.strip()})
            self.status.setText(f"ردیف {record.record_id} به {floor.strip()} کپی شد؛ برای ذخیره دائمی، دکمه ذخیره را بزن.")
        except Exception as exc:
            QMessageBox.warning(self, "کپی طبقه", str(exc))

    def delete_selected(self):
        record = self._selected_record()
        if record is None:
            self.status.setText("یک ردیف کامل را انتخاب کن.")
            return
        if record.record_id in self._saved_ids:
            QMessageBox.warning(self, "حذف متره", "حذف ردیف ذخیره‌شده از این پنجره مجاز نیست؛ ابتدا از مسیر مدیریت متره پروژه آن را اصلاح کن.")
            return
        self.workbench.remove_record(record.record_id)
        self._render_records()
        self._audit("delete_pending", {"record_id": record.record_id})
        self.status.setText("ردیف پیش‌نمایش حذف شد؛ با واگرد قابل بازیابی است.")

    def undo(self):
        if self.workbench is None or not self.workbench.can_undo:
            self.status.setText("عملیات قابل واگردی وجود ندارد.")
            return
        undo_target_ids = {row.record_id for row in self.workbench.undo_preview}
        if any(row.record_id in self._saved_ids and row.record_id not in undo_target_ids
               for row in self.workbench.records):
            self.status.setText("این واگرد ردیف ذخیره‌شده را از پیش‌نمایش خارج می‌کند؛ برای جلوگیری از مغایرت، عملیات متوقف شد.")
            return
        self.workbench.undo()
        self._render_records()
        self._audit("undo", {})
        self.status.setText("واگرد انجام شد.")

    def redo(self):
        if self.workbench is None or not self.workbench.can_redo:
            self.status.setText("عملیات قابل تکراری وجود ندارد.")
            return
        self.workbench.redo()
        self._render_records()
        self._audit("redo", {})
        self.status.setText("تکرار انجام شد.")

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
            self._session_id = uuid4().hex
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
        self._audit("preview_added", {"complete": added, "drafts": len(incomplete), "errors": len(row_errors)})
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
                    source_id=f"manual-workbench:{record.project_id}:{self._session_id}:{record.record_id}",
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
            self._audit("rows_saved", {"count": saved, "record_ids": sorted(self._saved_ids)})
            self.status.setText(f"{saved} ردیف در پروژه ذخیره شد." + ((" خطاها: " + " | ".join(errors)) if errors else ""))
        elif errors:
            self.status.setText("هیچ ردیفی ذخیره نشد: " + " | ".join(errors))
        else:
            self.status.setText("همه ردیف‌های کامل قبلاً ذخیره شده‌اند.")
