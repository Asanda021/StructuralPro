"""Interactive Windows takeoff canvas for PDF/CAD review.

The widget is intentionally lightweight: the geometry engine is deterministic
and the UI records every confirmed measurement with its scale and source.
"""
from __future__ import annotations
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QBrush
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLineEdit,QComboBox,QLabel,QGraphicsView,QGraphicsScene,QGraphicsLineItem,QGraphicsPolygonItem,QGraphicsEllipseItem,QDialog,QTableWidget,QTableWidgetItem
from core.drawings.graphical_takeoff import ScaleCalibration,Point,MeasurementStore

class TakeoffCanvas(QGraphicsView):
    def __init__(self,store,on_change=None):
        super().__init__(); self.store=store; self.on_change=on_change
        self.scene=QGraphicsScene(self); self.setScene(self.scene)
        self.setRenderHints(self.renderHints()); self.points=[]; self.mode="length"; self.scale=ScaleCalibration.parse("1:100")
        self.setSceneRect(0,0,1200,800); self._grid()
    def _grid(self):
        for x in range(0,1201,50): self.scene.addLine(x,0,x,800,QPen(Qt.GlobalColor.lightGray))
        for y in range(0,801,50): self.scene.addLine(0,y,1200,y,QPen(Qt.GlobalColor.lightGray))
    def set_scale(self,text): self.scale=ScaleCalibration.parse(text or "1:100")
    def set_mode(self,mode): self.mode=mode; self.points=[]
    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton: return super().mousePressEvent(event)
        p=self.mapToScene(event.position().toPoint()); self.points.append(Point(p.x(),p.y()))
        self.scene.addEllipse(p.x()-3,p.y()-3,6,6,QPen(Qt.GlobalColor.darkBlue),QBrush(Qt.GlobalColor.darkBlue))
        if self.mode=="count":
            self.store.add_count(1,source="windows-canvas",label="شمارش")
            self.points=[]; self._notify(); return
        if len(self.points)>1:
            a=self.points[-2]; b=self.points[-1]
            self.scene.addLine(a.x,a.y,b.x,b.y,QPen(Qt.GlobalColor.blue,2))
    def finish(self):
        if self.mode=="length" and len(self.points)>=2:
            self.store.add_length(self.points,self.scale,source="windows-canvas",label="متره طولی")
        elif self.mode=="area" and len(self.points)>=3:
            self.store.add_area(self.points,self.scale,source="windows-canvas",label="متره سطحی")
        self.points=[]; self._notify()
    def _notify(self):
        if self.on_change: self.on_change()

class GraphicalTakeoffDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("متره گرافیکی حرفه‌ای"); self.resize(1250,850)
        self.store=MeasurementStore(); root=QVBoxLayout(self)
        bar=QHBoxLayout(); bar.addWidget(QLabel("مقیاس:"))
        self.scale=QLineEdit("1:100"); self.scale.setMaximumWidth(100); bar.addWidget(self.scale)
        self.mode=QComboBox(); self.mode.addItems(["طول","مساحت","شمارش"]); bar.addWidget(self.mode)
        self.apply=QPushButton("اعمال ابزار"); self.finish=QPushButton("ثبت متره"); self.clear=QPushButton("پاک‌کردن")
        bar.addWidget(self.apply); bar.addWidget(self.finish); bar.addWidget(self.clear); root.addLayout(bar)
        self.canvas=TakeoffCanvas(self.store,self.refresh); root.addWidget(self.canvas,4)
        self.table=QTableWidget(0,5); self.table.setHorizontalHeaderLabels(["شناسه","نوع","مقدار","واحد","فرمول"]); root.addWidget(self.table,2)
        self.apply.clicked.connect(self.apply_tool); self.finish.clicked.connect(self.canvas.finish); self.clear.clicked.connect(self.clear_all)
    def apply_tool(self):
        self.canvas.set_scale(self.scale.text())
        self.canvas.set_mode({"طول":"length","مساحت":"area","شمارش":"count"}[self.mode.currentText()])
    def refresh(self):
        self.table.setRowCount(0)
        for i,x in enumerate(self.store.all()):
            self.table.insertRow(i)
            for j,v in enumerate([x.id,x.kind,round(x.value,4),x.unit,x.formula]):
                self.table.setItem(i,j,QTableWidgetItem(str(v)))
    def clear_all(self):
        self.store.clear(); self.canvas.scene.clear(); self.canvas.points=[]; self.canvas._grid(); self.refresh()
