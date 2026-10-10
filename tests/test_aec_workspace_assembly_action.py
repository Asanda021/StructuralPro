"""Real Qt button-to-project integration for multi-component AEC assemblies."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

try:
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
        QLineEdit, QMessageBox, QPushButton, QTableWidget,
    )
except (OSError, ImportError) as exc:
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)

from app.aec_workspace import build_aec_workspace
from core.platform.application import StructuralProApp
from core.pricing.catalog import PriceCatalog


@pytest.fixture
def ui(tmp_path, monkeypatch):
    qt = QApplication.instance() or QApplication([])
    service = StructuralProApp(tmp_path)
    service.create_project("ساختمان پنج طبقه", "test-p1")
    widget = build_aec_workspace(
        service, PriceCatalog(), title="بنایی", description="متره", domain="building",
        key="masonry",
    )
    widget.show()
    qt.processEvents()
    alerts = []
    monkeypatch.setattr(
        QMessageBox, "warning",
        lambda *args, **kwargs: alerts.append(("warning", args[2])),
    )
    monkeypatch.setattr(
        QMessageBox, "critical",
        lambda *args, **kwargs: alerts.append(("critical", args[2])),
    )
    yield widget, service, alerts
    widget.close()
    widget.deleteLater()
    qt.processEvents()
    service.store.close()


def _set(widget, field, value):
    spin = widget.findChild(QDoubleSpinBox, "TakeoffField_" + field)
    assert spin.isEnabled(), field
    spin.setValue(value)


def _choose_block_wall(widget):
    widget.findChild(QLineEdit, "TakeoffProject").setText("test-p1")
    combo = widget.findChild(QComboBox, "TakeoffItem")
    combo.setCurrentIndex(combo.findData("block_wall"))
    box = next(x for x in widget.findChildren(QCheckBox) if "Assembly" in x.text())
    box.setChecked(True)


def _fill_wall(widget):
    values = dict(
        length=10, height=3, thickness=0.2, openings=4,
        block_length=0.4, block_height=0.2, block_thickness=0.2,
        joint_thickness=0.01, cement_parts=1, sand_parts=4,
    )
    for field, value in values.items():
        _set(widget, field, value)


def _click(widget):
    widget.findChild(QPushButton, "PrimaryAction").click()
    QApplication.processEvents()


def test_assembly_button_persists_all_components_once_with_distinct_provenance(ui):
    widget, service, alerts = ui
    _choose_block_wall(widget)
    _fill_wall(widget)
    widget.findChild(QLineEdit, "TakeoffFloor").setText("طبقه اول")
    _click(widget)

    assert alerts == []
    project = service.open_project("test-p1")
    assert len(project["takeoff_assemblies"]) == 1
    assert len(project["takeoffs"]) == 5
    assert len(project["boq"]) == 5
    assert len({r["source_id"] for r in project["takeoffs"]}) == 5
    assert all(row["system"] == "طبقه اول" for row in project["takeoffs"])
    assert all(row["quantities"][0]["unit_price"] is None for row in project["takeoffs"])
    assert widget.findChild(QTableWidget).rowCount() == 5


def test_assembly_requires_explicit_floor_and_rejects_reused_price_code(ui):
    widget, service, alerts = ui
    _choose_block_wall(widget)
    _fill_wall(widget)
    _click(widget)
    assert any("طبقه" in message for _, message in alerts)
    assert service.open_project("test-p1")["takeoffs"] == []

    alerts.clear()
    widget.findChild(QLineEdit, "TakeoffFloor").setText("طبقه اول")
    # Disabled price input can retain a previously entered value when toggling.
    price = next(x for x in widget.findChildren(QLineEdit) if "فهرست‌بها" in x.placeholderText())
    price.setText("080101")
    _click(widget)
    assert any("همه اجزا" in message for _, message in alerts)
    assert service.open_project("test-p1")["boq"] == []


def test_joist_roof_assembly_uses_real_template_without_unrequested_mesh(tmp_path, monkeypatch):
    qt = QApplication.instance() or QApplication([])
    service = StructuralProApp(tmp_path)
    service.create_project("پروژه سقف تیرچه‌فوم", "roof-p1")
    widget = build_aec_workspace(
        service, PriceCatalog(), title="سازه بتن", description="متره",
        domain="building", key="structural_concrete",
    )
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warnings.append(a[2]))
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: warnings.append(a[2]))
    widget.show()
    qt.processEvents()
    combo = widget.findChild(QComboBox, "TakeoffItem")
    combo.setCurrentIndex(combo.findData("joist_foam_roof"))
    next(x for x in widget.findChildren(QCheckBox) if "Assembly" in x.text()).setChecked(True)
    widget.findChild(QLineEdit, "TakeoffProject").setText("roof-p1")
    widget.findChild(QLineEdit, "TakeoffFloor").setText("طبقه دوم")
    for field, val in {
        "count": 1, "length": 6, "width": 4,
        "topping_thickness": 0.05, "joist_spacing": 0.5,
        "joist_width": 0.1, "joist_depth": 0.2,
        "foam_length": 1, "foam_width": 0.5, "foam_height": 0.2,
    }.items():
        _set(widget, field, val)
    assert widget.findChild(QDoubleSpinBox, "TakeoffField_mesh_unit_weight").value() == 0
    _click(widget)
    assert warnings == []
    saved = service.open_project("roof-p1")
    assert len(saved["takeoff_assemblies"]) == 1
    assert saved["takeoff_assemblies"][0]["assembly_code"] == "joist_foam_roof_assembly"
    codes = {row["quantities"][0]["code"] for row in saved["takeoffs"]}
    assert codes == {"concrete", "joist", "foam"}
    assert "reinforcement_mesh" not in codes
    assert len(saved["boq"]) == 3
    widget.close()
    widget.deleteLater()
    qt.processEvents()
    service.store.close()
