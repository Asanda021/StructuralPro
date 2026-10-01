"""Professional Windows drawing takeoff workspace for StructuralPro."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QByteArray
from PySide6.QtGui import QPen, QBrush, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox,
    QLabel, QGraphicsView, QGraphicsScene, QDialog, QTableWidget,
    QTableWidgetItem, QSpinBox, QFileDialog, QMessageBox, QFrame,
    QDoubleSpinBox, QInputDialog, QHeaderView
)

from core.drawings.graphical_takeoff import Point
from core.drawings.pdf_engine import PDFDrawingEngine
from core.drawings.takeoff_session import DrawingTakeoffSession


class TakeoffCanvas(QGraphicsView):
    def __init__(self, session: DrawingTakeoffSession, on_change=None, on_note=None):
        super().__init__()
        self.session = session
        self.on_change = on_change
        self.on_note = on_note
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.points: list[Point] = []
        self.mode = "length"
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def set_mode(self, mode: str):
        self.mode = mode
        self.points = []

    def wheelEvent(self, event):
        self.scale_view(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)

    def scale_view(self, factor: float):
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        p = self.mapToScene(event.position().toPoint())
        page = self.session.current_page

        if self.mode == "note":
            if self.on_note:
                self.on_note(p.x(), p.y(), page)
            return

        point = Point(p.x(), p.y())
        self.points.append(point)
        self.scene.addEllipse(
            p.x() - 3, p.y() - 3, 6, 6,
            QPen(Qt.GlobalColor.darkBlue), QBrush(Qt.GlobalColor.darkBlue)
        )

        if self.mode == "count":
            self._commit_count()
            return

        if len(self.points) > 1:
            a, b = self.points[-2], self.points[-1]
            self.scene.addLine(
                a.x, a.y, b.x, b.y, QPen(Qt.GlobalColor.blue, 2)
            )

    def _commit_count(self):
        try:
            self.session.add_count(
                1, page=self.session.current_page, label="شمارش",
                source=f"page:{self.session.current_page}:count:{len(self.session.items)+1}"
            )
            self.points = []
            self._notify()
        except Exception as exc:
            QMessageBox.warning(self, "متره", str(exc))

    def finish(self):
        try:
            if self.mode == "length" and len(self.points) >= 2:
                self.session.add_length(
                    self.points, page=self.session.current_page, label="متره طولی",
                    source=f"page:{self.session.current_page}:length:{len(self.session.items)+1}"
                )
            elif self.mode == "area" and len(self.points) >= 3:
                self.session.add_area(
                    self.points, page=self.session.current_page, label="متره سطحی",
                    source=f"page:{self.session.current_page}:area:{len(self.session.items)+1}"
                )
            else:
                self.points = []
                return
            self.points = []
            self._notify()
        except Exception as exc:
            QMessageBox.warning(self, "ثبت متره", str(exc))

    def _draw_measurement(self, item):
        if item.kind == "length" and len(item.geometry) >= 2:
            pts = [QPointF(x, y) for x, y in item.geometry]
            for i in range(len(pts) - 1):
                self.scene.addLine(
                    pts[i].x(), pts[i].y(), pts[i + 1].x(), pts[i + 1].y(),
                    QPen(Qt.GlobalColor.blue, 3)
                )
        elif item.kind == "area" and len(item.geometry) >= 3:
            poly = QPolygonF([QPointF(x, y) for x, y in item.geometry])
            self.scene.addPolygon(
                poly, QPen(Qt.GlobalColor.darkBlue, 2),
                QBrush(Qt.GlobalColor.lightGray)
            )

    def _notify(self):
        if self.on_change:
            self.on_change()


class GraphicalTakeoffDialog(QDialog):
    def __init__(self, parent=None, pdf_path=""):
        super().__init__(parent)
        self.setWindowTitle("متره گرافیکی — نقشه‌محور")
        self.resize(1450, 920)
        self.session = DrawingTakeoffSession(pdf_path)
        self.pdf_path = pdf_path
        self.engine = None
        self.page = 1

        root = QVBoxLayout(self)
        toolbar = QFrame()
        toolbar.setObjectName("DashboardCard")
        header = QHBoxLayout(toolbar)
        header.setContentsMargins(12, 10, 12, 10)

        header.addWidget(QLabel("ابزار:"))
        self.mode = QComboBox()
        self.mode.addItems(["طول", "مساحت", "شمارش", "یادداشت"])
        header.addWidget(self.mode)

        self.scale_label = QLabel("مقیاس: 0.010000 m/px")
        self.calibrate = QPushButton("کالیبراسیون")
        self.calibrate.setObjectName("SecondaryAction")
        header.addWidget(self.scale_label)
        header.addWidget(self.calibrate)

        self.open_pdf = QPushButton("بازکردن PDF")
        self.prev = QPushButton("صفحه قبلی")
        self.next = QPushButton("صفحه بعدی")
        self.page_no = QSpinBox()
        self.page_no.setMinimum(1)
        self.page_no.setMaximum(9999)
        self.page_no.setPrefix("صفحه ")
        self.zoom_out = QPushButton("−")
        self.zoom_in = QPushButton("+")
        self.fit = QPushButton("نمایش کامل")
        self.finish = QPushButton("ثبت متره")
        self.undo = QPushButton("↶ واگرد")
        self.redo = QPushButton("↷ تکرار")
        self.delete = QPushButton("حذف انتخاب")
        for x in [
            self.open_pdf, self.prev, self.next, self.page_no,
            self.zoom_out, self.zoom_in, self.fit, self.undo, self.redo,
            self.delete, self.finish
        ]:
            header.addWidget(x)
        root.addWidget(toolbar)

        self.canvas = TakeoffCanvas(self.session, self.refresh, self.add_note)
        self.canvas.setFrameShape(QFrame.Shape.StyledPanel)
        root.addWidget(self.canvas, 5)

        table_title = QLabel("متره‌های ثبت‌شده — قابل بازبینی و اتصال به BOQ")
        table_title.setObjectName("SectionTitle")
        root.addWidget(table_title)

        self.table = QTableWidget(0, 8)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalHeaderLabels([
            "شناسه", "صفحه", "نوع", "شرح", "مقدار", "واحد", "کد BOQ", "منبع"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.table, 2)

        self.status = QLabel("برای شروع، نقشه را باز کنید و مقیاس را کالیبره کنید.")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.mode.currentTextChanged.connect(self.apply_tool)
        self.calibrate.clicked.connect(self.calibrate_scale)
        self.open_pdf.clicked.connect(self.select_pdf)
        self.prev.clicked.connect(lambda: self.load_page(self.page - 1))
        self.next.clicked.connect(lambda: self.load_page(self.page + 1))
        self.page_no.valueChanged.connect(self.load_page)
        self.zoom_in.clicked.connect(lambda: self.canvas.scale_view(1.25))
        self.zoom_out.clicked.connect(lambda: self.canvas.scale_view(0.8))
        self.fit.clicked.connect(self.reset_zoom)
        self.finish.clicked.connect(self.canvas.finish)
        self.undo.clicked.connect(self.undo_session)
        self.redo.clicked.connect(self.redo_session)
        self.delete.clicked.connect(self.delete_selected)

        if pdf_path:
            try:
                self.engine = PDFDrawingEngine(pdf_path)
                self.page_no.setMaximum(self.engine.page_count)
                self.load_page(1)
            except Exception as exc:
                QMessageBox.warning(self, "PDF", "فایل برای نمایش گرافیکی باز نشد: " + str(exc))

    def select_pdf(self):
        path = QFileDialog.getOpenFileName(
            self, "انتخاب نقشه PDF", "", "PDF (*.pdf)"
        )[0]
        if not path:
            return
        try:
            self.engine = PDFDrawingEngine(path)
            self.pdf_path = path
            self.session.drawing_source = path
            self.page_no.setMaximum(self.engine.page_count)
            self.load_page(1)
        except Exception as exc:
            QMessageBox.critical(self, "خطای PDF", str(exc))

    def load_page(self, page):
        if not self.engine or page < 1 or page > self.engine.page_count:
            return
        try:
            self.page = int(page)
            self.session.set_page(self.page)
            self.page_no.blockSignals(True)
            self.page_no.setValue(self.page)
            self.page_no.blockSignals(False)

            data = self.engine.render(self.page, 150)
            pix = QPixmap()
            pix.loadFromData(QByteArray(data), "PNG")
            self.canvas.scene.clear()
            self.canvas.scene.addPixmap(pix)
            self.canvas.setSceneRect(0, 0, pix.width(), pix.height())
            self.canvas.points = []
            for item in self.session.for_page(self.page):
                self.canvas._draw_measurement(item)
            self.refresh()
            self.reset_zoom()
        except Exception as exc:
            QMessageBox.critical(self, "خطای نمایش PDF", str(exc))

    def reset_zoom(self):
        self.canvas.resetTransform()
        if self.canvas.scene.sceneRect().isValid():
            self.canvas.fitInView(
                self.canvas.scene.sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )

    def apply_tool(self):
        mapping = {
            "طول": "length", "مساحت": "area",
            "شمارش": "count", "یادداشت": "note"
        }
        self.canvas.set_mode(mapping[self.mode.currentText()])
        self.status.setText(
            f"ابزار فعال: {self.mode.currentText()} | صفحه {self.page}"
        )

    def calibrate_scale(self):
        px, ok = QInputDialog.getDouble(
            self, "کالیبراسیون مقیاس",
            "فاصله روی نقشه (پیکسل):", 1000.0, 0.001, 100000000.0, 3
        )
        if not ok:
            return
        meters, ok = QInputDialog.getDouble(
            self, "کالیبراسیون مقیاس",
            "فاصله واقعی (متر):", 10.0, 0.001, 100000000.0, 3
        )
        if not ok:
            return
        try:
            cal = self.session.calibrate(self.page, px, meters)
            self.scale_label.setText(
                f"مقیاس: {cal.meters_per_pixel:.6f} m/px"
            )
            self.status.setText(
                f"کالیبراسیون ثبت شد | {px:g} px = {meters:g} m"
            )
            self.undo.setEnabled(self.session.can_undo)
        except Exception as exc:
            QMessageBox.warning(self, "کالیبراسیون", str(exc))

    def add_note(self, x, y, page):
        text, ok = QInputDialog.getText(self, "یادداشت نقشه", "متن یادداشت:")
        if not ok or not text.strip():
            return
        try:
            self.session.add_note(text, x, y, page=page)
            self.status.setText(f"یادداشت در صفحه {page} ثبت شد.")
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "یادداشت", str(exc))

    def undo_session(self):
        if self.session.undo():
            self.redraw_current_page()
            self.refresh()

    def redo_session(self):
        if self.session.redo():
            self.redraw_current_page()
            self.refresh()

    def delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            self.status.setText("یک متره را از جدول انتخاب کنید.")
            return
        item_id = self.table.item(row, 0)
        if not item_id:
            return
        if self.session.remove(item_id.text()):
            self.redraw_current_page()
            self.refresh()

    def redraw_current_page(self):
        if not self.engine:
            return
        data = self.engine.render(self.page, 150)
        pix = QPixmap()
        pix.loadFromData(QByteArray(data), "PNG")
        self.canvas.scene.clear()
        self.canvas.scene.addPixmap(pix)
        self.canvas.setSceneRect(0, 0, pix.width(), pix.height())
        self.canvas.points = []
        for item in self.session.for_page(self.page):
            self.canvas._draw_measurement(item)

    def refresh(self):
        self.table.setRowCount(0)
        for i, item in enumerate(self.session.items):
            self.table.insertRow(i)
            values = [
                item.id, item.page, item.kind, item.label or item.takeoff_code,
                round(item.quantity, 4), item.unit, item.takeoff_code or "—",
                item.source_ref,
            ]
            for j, value in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

        valid = self.session.validate()
        state = "🟢 معتبر" if valid["valid"] else "🟠 نیازمند بررسی"
        self.status.setText(
            f"{state} | متره‌ها: {len(self.session.items)} | "
            f"واگرد: {'فعال' if self.session.can_undo else '—'} | "
            f"تکرار: {'فعال' if self.session.can_redo else '—'}"
        )
        self.undo.setEnabled(self.session.can_undo)
        self.redo.setEnabled(self.session.can_redo)
