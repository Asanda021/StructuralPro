"""Exercise the actual manual form rather than matching its source code."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
try:
    from PySide6.QtWidgets import QApplication, QComboBox, QDoubleSpinBox, QLineEdit, QPushButton, QScrollArea
    from PySide6.QtCore import QRect
except (ImportError, OSError) as exc:
    pytest.skip(f"Qt runtime is unavailable: {exc}", allow_module_level=True)
from app.aec_workspace import build_aec_workspace, ITEMS


@pytest.fixture
def workspace():
    app = QApplication.instance() or QApplication([])
    widget = build_aec_workspace(None, None, title="بتن", description="متره", domain="building", key="structural_concrete")
    widget.resize(900, 640)
    widget.show()
    app.processEvents()
    yield widget
    widget.close()
    widget.deleteLater()
    app.processEvents()


def field(widget, name):
    return widget.findChild(QDoubleSpinBox, "TakeoffField_" + name)


def test_only_selected_member_inputs_and_labels_are_visible(workspace):
    combo = workspace.findChild(QComboBox, "TakeoffItem")
    for code, _, names in ITEMS["structural_concrete"]:
        combo.setCurrentIndex(combo.findData(code))
        QApplication.processEvents()
        for value in workspace.findChildren(QDoubleSpinBox):
            active = value.objectName().removeprefix("TakeoffField_") in names
            assert value.isVisible() == active
            assert value.isEnabled() == active
            assert value.parentWidget().layout().labelForField(value).isVisible() == active
    scroll = workspace.findChild(QScrollArea, "TakeoffFormScroll")
    assert scroll.widgetResizable()
    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
    QApplication.processEvents()
    button = workspace.findChild(QPushButton, "PrimaryAction")
    assert button.isVisible()
    button_rect = QRect(button.mapTo(scroll.viewport(), button.rect().topLeft()), button.size())
    assert scroll.viewport().rect().contains(button_rect)


def apply_quick(widget, text):
    entry = next(x for x in widget.findChildren(QLineEdit) if x.placeholderText().startswith("مثال:"))
    entry.setText(text)
    next(x for x in widget.findChildren(QPushButton) if x.text() == "اعمال ورودی سریع").click()


def test_new_incomplete_quick_draft_does_not_reuse_previous_dimensions(workspace):
    apply_quick(workspace, "ستون: تعداد=2، عرض=0.5، عمق=0.5، ارتفاع=3")
    assert field(workspace, "height").value() == 3
    apply_quick(workspace, "ستون: تعداد=2، عرض=0.4، عمق=0.4")
    assert field(workspace, "height").value() == 0
    assert field(workspace, "width").value() == .4
    apply_quick(workspace, "ستون: عرض=0.4، عمق=0.4، ارتفاع=3")
    assert field(workspace, "count").value() == 0


def test_batch_is_rejected_without_partially_applying_first_row(workspace):
    field(workspace, "length").setValue(8)
    combo = workspace.findChild(QComboBox, "TakeoffItem")
    previous = combo.currentData()
    apply_quick(workspace, "ستون: تعداد=2، عرض=0.5، عمق=0.5، ارتفاع=3; تیر: تعداد=1، طول=6، عرض=0.3، عمق=0.5")
    assert combo.currentData() == previous
    assert field(workspace, "length").value() == 8


class _TakeoffService:
    def __init__(self, *, fail_first=False, fail_open=False):
        self.sources = []
        self.fail_first = fail_first
        self.fail_open = fail_open

    def open_project(self, project_id):
        if self.fail_open:
            raise OSError("database unavailable")
        return {"takeoffs": []}

    def add_takeoff(self, project_id, domain, code, **params):
        self.sources.append(params["source_id"])
        if self.fail_first and len(self.sources) == 1:
            raise OSError("write failed")
        return {"quantities": [{"amount": 1.0, "unit": "m3", "formula": "test"}]}


def _calculation_workspace(service):
    return build_aec_workspace(
        service, None, title="بتن", description="متره",
        domain="building", key="structural_concrete",
    )


def _prepare_column(widget):
    combo = widget.findChild(QComboBox, "TakeoffItem")
    combo.setCurrentIndex(combo.findData("column"))
    field(widget, "width").setValue(.4)
    field(widget, "depth").setValue(.4)
    field(widget, "height").setValue(3)
    field(widget, "count").setValue(1)
    widget.findChild(QLineEdit, "TakeoffProject").setText("project-1")


def test_calculation_retry_reuses_source_identity_after_failed_write(monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    service = _TakeoffService(fail_first=True)
    widget = _calculation_workspace(service)
    _prepare_column(widget)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: None)
    button = widget.findChild(QPushButton, "PrimaryAction")
    button.click()
    button.click()
    assert len(service.sources) == 2
    assert service.sources[0] == service.sources[1]
    widget.close()


def test_refresh_clears_stale_rows_and_reports_read_error(monkeypatch):
    from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem
    service = _TakeoffService(fail_open=True)
    widget = _calculation_workspace(service)
    project = widget.findChild(QLineEdit, "TakeoffProject")
    project.setText("project-1")
    table = widget.findChild(QTableWidget)
    table.setRowCount(1)
    table.setItem(0, 0, QTableWidgetItem("stale"))
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    project.editingFinished.emit()
    assert table.rowCount() == 0
    assert warnings and "بارگذاری" in warnings[0][2]
    widget.close()
