"""Interactive professional PDF takeoff canvas for StructuralPro."""
from __future__ import annotations
from PySide6.QtCore import Qt, QPointF, QByteArray
from PySide6.QtGui import QPen, QBrush, QPixmap, QPolygonF
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLineEdit,QComboBox,QLabel,QGraphicsView,QGraphicsScene,QDialog,QTableWidget,QTableWidgetItem,QSpinBox,QFileDialog,QMessageBox,QFrame,QDoubleSpinBox
from core.drawings.graphical_takeoff import ScaleCalibration,Point,MeasurementStore
from core.drawings.pdf_engine import PDFDrawingEngine

class TakeoffCanvas(QGraphicsView):
    def __init__(self,store,on_change=None):
        super().__init__(); self.store=store; self.on_change=on_change
        self.scene=QGraphicsScene(self); self.setScene(self.scene); self.points=[]; self.mode="length"
        self.scale=ScaleCalibration(0.01,"m","m","0.01 m/px","pixel-calibration")
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag); self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    def set_scale(self,text):
        text=(text or "").strip()
        if text.endswith("m/px"):
            self.scale=ScaleCalibration(float(text[:-4].strip()),"m","m",text,"pixel-calibration")
        elif text:
            self.scale=ScaleCalibration.parse(text)
    def set_mode(self,mode): self.mode=mode; self.points=[]
    def wheelEvent(self,event):
        self.scale_view(1.15 if event.angleDelta().y()>0 else 1/1.15)
    def scale_view(self,factor): self.scale(factor,factor)
    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton: return super().mousePressEvent(event)
        p=self.mapToScene(event.position().toPoint()); self.points.append(Point(p.x(),p.y()))
        self.scene.addEllipse(p.x()-3,p.y()-3,6,6,QPen(Qt.GlobalColor.darkBlue),QBrush(Qt.GlobalColor.darkBlue))
        if self.mode=="count":
            item=self.store.add_count(1,source="windows-canvas",label="شمارش",page=getattr(self,"current_page",None))
            self._draw_measurement(item); self.points=[]; self._notify(); return
        if len(self.points)>1:
            a=self.points[-2]; b=self.points[-1]; self.scene.addLine(a.x,a.y,b.x,b.y,QPen(Qt.GlobalColor.blue,2))
    def finish(self):
        item=None
        if self.mode=="length" and len(self.points)>=2:
            item=self.store.add_length(self.points,self.scale,source="windows-canvas",label="متره طولی",page=getattr(self,"current_page",None))
        elif self.mode=="area" and len(self.points)>=3:
            item=self.store.add_area(self.points,self.scale,source="windows-canvas",label="متره سطحی",page=getattr(self,"current_page",None))
        self.points=[]
        if item: self._draw_measurement(item)
        self._notify()
    def _draw_measurement(self,item):
        if item.kind=="length" and len(item.geometry)>=2:
            pts=[QPointF(x,y) for x,y in item.geometry]
            for i in range(len(pts)-1): self.scene.addLine(pts[i].x(),pts[i].y(),pts[i+1].x(),pts[i+1].y(),QPen(Qt.GlobalColor.blue,3))
        elif item.kind=="area" and len(item.geometry)>=3:
            poly=QPolygonF([QPointF(x,y) for x,y in item.geometry])
            self.scene.addPolygon(poly,QPen(Qt.GlobalColor.darkBlue,2),QBrush(Qt.GlobalColor.lightGray))
    def _notify(self):
        if self.on_change: self.on_change()

class GraphicalTakeoffDialog(QDialog):
    def __init__(self,parent=None,pdf_path=""):
        super().__init__(parent); self.setWindowTitle("متره گرافیکی حرفه‌ای"); self.resize(1350,900)
        self.store=MeasurementStore(); self.pdf_path=pdf_path; self.engine=None; self.page=1
        root=QVBoxLayout(self); header=QHBoxLayout()
        header.addWidget(QLabel("مقیاس:")); self.scale=QLineEdit("0.01 m/px"); self.scale.setToolTip("کالیبراسیون پیکسل نقشه: مثال 1000px = 10m یعنی 0.01 m/px"); header.addWidget(self.scale)
        self.mode=QComboBox(); self.mode.addItems(["طول","مساحت","شمارش"]); header.addWidget(self.mode)
        self.apply=QPushButton("اعمال ابزار"); self.finish=QPushButton("ثبت متره"); self.clear=QPushButton("پاک‌کردن"); self.open_pdf=QPushButton("بازکردن PDF")
        self.prev=QPushButton("صفحه قبلی"); self.next=QPushButton("صفحه بعدی"); self.zoom=QPushButton("بازنشانی زوم")
        self.page_no=QSpinBox(); self.page_no.setMinimum(1); self.page_no.setMaximum(9999); self.page_no.setPrefix("صفحه ")
        for x in [self.open_pdf,self.prev,self.next,self.page_no,self.zoom,self.apply,self.finish,self.clear]: header.addWidget(x)
        root.addLayout(header)
        self.canvas=TakeoffCanvas(self.store,self.refresh); self.canvas.setFrameShape(QFrame.Shape.StyledPanel); root.addWidget(self.canvas,4)
        self.table=QTableWidget(0,6); self.table.setAlternatingRowColors(True); self.table.setHorizontalHeaderLabels(["شناسه","صفحه","نوع","مقدار","واحد","فرمول"]); root.addWidget(self.table,2)
        self.apply.clicked.connect(self.apply_tool); self.finish.clicked.connect(self.canvas.finish); self.clear.clicked.connect(self.clear_all)
        self.open_pdf.clicked.connect(self.select_pdf); self.prev.clicked.connect(lambda: self.load_page(self.page-1)); self.next.clicked.connect(lambda: self.load_page(self.page+1)); self.zoom.clicked.connect(self.reset_zoom); self.page_no.valueChanged.connect(self.load_page)
        if pdf_path:
            try: self.engine=PDFDrawingEngine(pdf_path); self.page_no.setMaximum(self.engine.page_count); self.load_page(1)
            except Exception as e: QMessageBox.warning(self,"PDF","فایل برای نمایش گرافیکی باز نشد: "+str(e))
    def select_pdf(self):
        path=QFileDialog.getOpenFileName(self,"انتخاب نقشه PDF","","PDF (*.pdf)")[0]
        if not path:return
        try:
            self.engine=PDFDrawingEngine(path); self.pdf_path=path; self.page_no.setMaximum(self.engine.page_count); self.load_page(1)
        except Exception as e: QMessageBox.critical(self,"خطای PDF",str(e))
    def load_page(self,page):
        if not self.engine or page<1 or page>self.engine.page_count:return
        try:
            self.page=page; self.page_no.blockSignals(True); self.page_no.setValue(page); self.page_no.blockSignals(False)
            data=self.engine.render(page,150); pix=QPixmap(); pix.loadFromData(QByteArray(data),"PNG")
            self.canvas.scene.clear(); self.canvas.scene.addPixmap(pix); self.canvas.setSceneRect(0,0,pix.width(),pix.height()); self.canvas.points=[]; self.canvas.current_page=page
            for item in self.store.all():
                if item.page==page: self.canvas._draw_measurement(item)
            self.refresh(); self.reset_zoom()
        except Exception as e: QMessageBox.critical(self,"خطای نمایش PDF",str(e))
    def reset_zoom(self):
        self.canvas.resetTransform()
        if self.canvas.scene.sceneRect().isValid(): self.canvas.fitInView(self.canvas.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
    def apply_tool(self):
        try: self.canvas.set_scale(self.scale.text())
        except Exception as e: QMessageBox.warning(self,"مقیاس",str(e)); return
        self.canvas.set_mode({"طول":"length","مساحت":"area","شمارش":"count"}[self.mode.currentText()])
    def refresh(self):
        self.table.setRowCount(0)
        for i,x in enumerate(self.store.all()):
            self.table.insertRow(i)
            for j,v in enumerate([x.id,x.page or "-",x.kind,round(x.value,4),x.unit,x.formula]):
                self.table.setItem(i,j,QTableWidgetItem(str(v)))
    def clear_all(self):
        self.store.clear(); self.canvas.points=[]; self.refresh()
        if self.engine:self.load_page(self.page)
        else:self.canvas.scene.clear()
