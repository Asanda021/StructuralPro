"""Professional Windows drawing takeoff workspace for StructuralPro."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QByteArray
from PySide6.QtGui import QPen, QBrush, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox,
    QLabel, QGraphicsView, QGraphicsScene, QDialog, QTableWidget,
    QTableWidgetItem, QSpinBox, QFileDialog, QMessageBox, QFrame,
    QDoubleSpinBox, QInputDialog, QHeaderView, QRubberBand
)

from core.drawings.graphical_takeoff import Point
from core.drawings.pdf_engine import PDFDrawingEngine
from core.drawings.takeoff_session import DrawingTakeoffSession
from core.drawings.viewer_model import DrawingViewerModel
from core.drawings.viewport_tools import ViewportRect


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
        self._previous_mode = "length"
        self._selection_origin = None
        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())
        self._region_overlay = None
        self.on_tool_status = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def set_mode(self, mode: str):
        if mode in {"zoom_window", "region_select"} and self.mode not in {"zoom_window", "region_select"}:
            self._previous_mode = self.mode
        self.cancel_interaction(reset_tool=False, announce=False)
        self.mode = mode
        self.points = []
        if mode in {"zoom_window", "region_select"}:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.unsetCursor()

    def _announce_tool(self, message: str):
        if self.on_tool_status:
            self.on_tool_status(message)

    def clear_region_selection(self):
        if self._region_overlay is not None:
            self.scene.removeItem(self._region_overlay)
            self._region_overlay = None

    def cancel_interaction(self, reset_tool: bool = True, announce: bool = True):
        self._selection_origin = None
        self._rubber_band.hide()
        self.points = []
        self.clear_region_selection()
        if reset_tool and self.mode in {"zoom_window", "region_select"}:
            self.mode = self._previous_mode
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.unsetCursor()
        if announce:
            self._announce_tool("عملیات انتخاب لغو شد؛ نمای نقشه تغییر نکرد.")

    def wheelEvent(self, event):
        self.scale_view(1.15 if event.angleDelta().y() > 0 else 1 / 1.15)

    def scale_view(self, factor: float):
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self.mode in {"zoom_window", "region_select"}:
            self.cancel_interaction()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        if self.mode in {"zoom_window", "region_select"}:
            self._selection_origin = event.position().toPoint()
            self._rubber_band.setGeometry(QRect(self._selection_origin, self._selection_origin))
            self._rubber_band.show()
            self.setFocus()
            return
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

    def mouseMoveEvent(self, event):
        if self._selection_origin is not None:
            self._rubber_band.setGeometry(
                QRect(self._selection_origin, event.position().toPoint()).normalized()
            )
            return
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selection_origin is not None:
            viewport_rect = QRect(self._selection_origin, event.position().toPoint()).normalized()
            self._selection_origin = None
            self._rubber_band.hide()
            top_left = self.mapToScene(viewport_rect.topLeft())
            bottom_right = self.mapToScene(viewport_rect.bottomRight())
            bounds = self.scene.sceneRect()
            selected = ViewportRect.from_points(
                top_left.x(), top_left.y(), bottom_right.x(), bottom_right.y()
            ).clamped(ViewportRect(bounds.left(), bounds.top(), bounds.right(), bounds.bottom()))
            if not selected.is_usable():
                self._announce_tool("ناحیه خیلی کوچک است؛ مستطیل بزرگ‌تری انتخاب کن یا لغو کن.")
                return
            scene_rect = QRectF(selected.left, selected.top, selected.width, selected.height)
            if self.mode == "zoom_window":
                self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
                self._announce_tool("بزرگ‌نمایی ناحیه انجام شد؛ برای بازگشت «نمایش کامل» را بزن.")
            else:
                self.clear_region_selection()
                pen = QPen(Qt.GlobalColor.darkGreen, 2, Qt.PenStyle.DashLine)
                self._region_overlay = self.scene.addRect(scene_rect, pen)
                self._announce_tool(
                    f"ناحیه انتخاب شد | عرض: {selected.width:.2f} | ارتفاع: {selected.height:.2f} واحد صحنه"
                )
            return
        return super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_interaction()
            event.accept()
            return
        return super().keyPressEvent(event)

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
        self.viewer = DrawingViewerModel()
        self.cad_document = None
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

        self.open_pdf = QPushButton("بازکردن نقشه")
        self.prev = QPushButton("صفحه قبلی")
        self.next = QPushButton("صفحه بعدی")
        self.page_no = QSpinBox()
        self.page_no.setMinimum(1)
        self.page_no.setMaximum(9999)
        self.page_no.setPrefix("صفحه ")
        self.zoom_out = QPushButton("−")
        self.zoom_in = QPushButton("+")
        self.fit = QPushButton("نمایش کامل")
        self.zoom_window = QPushButton("Zoom Window")
        self.select_region = QPushButton("انتخاب ناحیه")
        self.cancel_selection = QPushButton("لغو انتخاب")
        self.source_label = QLabel("منبع: —")
        self.finish = QPushButton("ثبت متره")
        self.undo = QPushButton("↶ واگرد")
        self.redo = QPushButton("↷ تکرار")
        self.delete = QPushButton("حذف انتخاب")
        for x in [
            self.open_pdf, self.prev, self.next, self.page_no,
            self.zoom_out, self.zoom_in, self.fit, self.zoom_window,
            self.select_region, self.cancel_selection, self.undo, self.redo,
            self.delete, self.finish
        ]:
            header.addWidget(x)
        header.addWidget(self.source_label)
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
        self.canvas.on_tool_status = self.status.setText

        self.mode.currentTextChanged.connect(self.apply_tool)
        self.calibrate.clicked.connect(self.calibrate_scale)
        self.open_pdf.clicked.connect(self.select_drawing)
        self.prev.clicked.connect(lambda: self.load_page(self.page - 1))
        self.next.clicked.connect(lambda: self.load_page(self.page + 1))
        self.page_no.valueChanged.connect(self.load_page)
        self.zoom_in.clicked.connect(lambda: self.canvas.scale_view(1.25))
        self.zoom_out.clicked.connect(lambda: self.canvas.scale_view(0.8))
        self.fit.clicked.connect(self.reset_zoom)
        self.zoom_window.clicked.connect(
            lambda: self._activate_view_tool("zoom_window", "مستطیل ناحیه بزرگ‌نمایی را با ماوس بکش؛ Esc یا کلیک راست لغو می‌کند.")
        )
        self.select_region.clicked.connect(
            lambda: self._activate_view_tool("region_select", "مستطیل ناحیه موردنظر را با ماوس بکش؛ Esc یا کلیک راست لغو می‌کند.")
        )
        self.cancel_selection.clicked.connect(lambda: self.canvas.cancel_interaction())
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

    def select_drawing(self):
        path = QFileDialog.getOpenFileName(
            self, "انتخاب نقشه", "", "نقشه‌ها (*.pdf *.dwg *.dxf);;PDF (*.pdf);;CAD (*.dwg *.dxf);;همه فایل‌ها (*)"
        )[0]
        if not path:
            return
        try:
            self.open_drawing(path)
        except Exception as exc:
            QMessageBox.critical(self, "خطای نقشه", str(exc))

    def select_pdf(self):
        self.select_drawing()

    def open_drawing(self, path):
        self.viewer.open(path)
        self.pdf_path = str(path)
        self.session.drawing_source = str(path)
        self.source_label.setText(f"منبع: {self.viewer.source_name} | {self.viewer.kind.upper()}")
        self.page_no.setMaximum(max(1, self.viewer.page_count))
        self.cad_document = self.viewer.cad_document
        self.engine = PDFDrawingEngine(path) if self.viewer.kind == "pdf" else None
        self.load_page(1)

    def load_page(self, page):
        if not self.viewer.path or page < 1 or page > max(1, self.viewer.page_count):
            return
        try:
            self.page = int(page)
            self.session.set_page(self.page)
            self.page_no.blockSignals(True)
            self.page_no.setValue(self.page)
            self.page_no.blockSignals(False)

            self.canvas.scene.clear()
            self.canvas._region_overlay = None
            self.canvas.points = []
            if self.viewer.kind == "pdf":
                data = self.engine.render(self.page, 150)
                pix = QPixmap()
                if not pix.loadFromData(QByteArray(data), "PNG"):
                    raise RuntimeError("رندر PDF ناموفق بود.")
                self.canvas.scene.addPixmap(pix)
                self.canvas.setSceneRect(0, 0, pix.width(), pix.height())
                for item in self.session.for_page(self.page):
                    self.canvas._draw_measurement(item)
            else:
                self._render_cad()
            self.refresh()
            self.reset_zoom()
        except Exception as exc:
            QMessageBox.critical(self, "خطای نمایش PDF", str(exc))

    def _render_cad(self):
        doc = self.cad_document
        if doc is None:
            raise RuntimeError("سند CAD برای نمایش آماده نیست.")
        coords=[]
        for entity in doc.entities:
            data=entity.data
            coords.extend((float(x),float(y)) for x,y in data.get("points",[]))
            for key in ("start","end","center","insert"):
                if key in data and data[key] is not None:
                    coords.append((float(data[key][0]),float(data[key][1])))
        if not coords:
            self.canvas.scene.addText("CAD فاقد هندسه قابل نمایش است.")
            self.canvas.setSceneRect(0,0,1000,700)
            return
        min_x=min(x for x,_ in coords); max_x=max(x for x,_ in coords)
        min_y=min(y for _,y in coords); max_y=max(y for _,y in coords)
        margin=max(max_x-min_x,max_y-min_y,1.0)*0.05
        min_x-=margin; max_x+=margin; min_y-=margin; max_y+=margin
        def sx(x): return x-min_x
        def sy(y): return max_y-y
        pen=QPen(Qt.GlobalColor.darkBlue,0)
        for entity in doc.entities:
            d=entity.data
            if entity.entity_type=="LINE" and d.get("start") and d.get("end"):
                a,b=d["start"],d["end"]
                self.canvas.scene.addLine(sx(a[0]),sy(a[1]),sx(b[0]),sy(b[1]),pen)
            elif entity.entity_type in {"LWPOLYLINE","POLYLINE"} and len(d.get("points",[]))>=2:
                pts=[QPointF(sx(x),sy(y)) for x,y in d["points"]]
                if len(pts)>=3: self.canvas.scene.addPolygon(QPolygonF(pts),pen)
                else: self.canvas.scene.addLine(pts[0].x(),pts[0].y(),pts[-1].x(),pts[-1].y(),pen)
            elif entity.entity_type=="CIRCLE" and d.get("center") and d.get("radius"):
                x,y=d["center"]; r=float(d["radius"])
                self.canvas.scene.addEllipse(sx(x-r),sy(y+r),2*r,2*r,pen)
            elif entity.entity_type in {"TEXT","MTEXT"} and d.get("text"):
                pos=d.get("insert",d.get("start",(0,0)))
                item=self.canvas.scene.addText(str(d["text"])); item.setPos(sx(pos[0]),sy(pos[1]))
        self.canvas.setSceneRect(0,0,max_x-min_x,max_y-min_y)
        self.status.setText(f"🟢 CAD نمایش داده شد | {len(doc.entities)} المان | لایه‌ها: {len(doc.layers)} | واحد: {doc.units}")

    def _activate_view_tool(self, mode: str, instruction: str):
        self.canvas.set_mode(mode)
        self.status.setText(instruction)

    def reset_zoom(self):
        self.canvas.cancel_interaction(reset_tool=True, announce=False)
        self.canvas.clear_region_selection()
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
        if not self.viewer.path:
            return
        self.canvas.scene.clear()
        self.canvas._region_overlay = None
        if self.viewer.kind == "pdf":
            data = self.engine.render(self.page, 150)
            pix = QPixmap()
            pix.loadFromData(QByteArray(data), "PNG")
            self.canvas.scene.addPixmap(pix)
            self.canvas.setSceneRect(0, 0, pix.width(), pix.height())
            for item in self.session.for_page(self.page):
                self.canvas._draw_measurement(item)
        else:
            self._render_cad()

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
