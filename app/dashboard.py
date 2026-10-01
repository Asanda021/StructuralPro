"""Commercial dashboard widgets for StructuralPro Windows UI."""
from __future__ import annotations
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QFrame,QTableWidget,QTableWidgetItem,QHeaderView

def _card(title, value, hint):
    f=QFrame(); f.setObjectName("KpiCard")
    v=QVBoxLayout(f); v.setContentsMargins(16,14,16,14); v.setSpacing(4)
    t=QLabel(title); t.setObjectName("KpiTitle")
    n=QLabel(value); n.setObjectName("KpiValue")
    h=QLabel(hint); h.setObjectName("KpiHint"); h.setWordWrap(True)
    v.addWidget(t); v.addWidget(n); v.addWidget(h)
    return f

class DashboardPage(QWidget):
    def __init__(self, service, catalog, on_open_page=None):
        super().__init__(); self.service=service; self.catalog=catalog; self.on_open_page=on_open_page
        root=QVBoxLayout(self); root.setContentsMargins(24,20,24,20); root.setSpacing(14)
        title=QLabel("داشبورد"); title.setObjectName("PageTitle")
        desc=QLabel("نمای عملیاتی پروژه‌ها، متره، نقشه‌ها و وضعیت داده‌های مالی"); desc.setObjectName("PageDescription")
        root.addWidget(title); root.addWidget(desc)
        self.cards=QGridLayout(); self.cards.setSpacing(12); root.addLayout(self.cards)
        body=QHBoxLayout(); body.setSpacing(14)
        left=QFrame(); left.setObjectName("DashboardCard"); lv=QVBoxLayout(left)
        lt=QLabel("پروژه‌های اخیر"); lt.setObjectName("SectionTitle"); lv.addWidget(lt)
        self.table=QTableWidget(0,3); self.table.setHorizontalHeaderLabels(["شناسه","نام پروژه","وضعیت"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True); lv.addWidget(self.table)
        right=QFrame(); right.setObjectName("DashboardCard"); rv=QVBoxLayout(right)
        rt=QLabel("اقدامات سریع"); rt.setObjectName("SectionTitle"); rv.addWidget(rt)
        for label,idx in [("➕ پروژه جدید",1),("📐 متره گرافیکی",3),("💰 فهرست‌بها",4),("📄 گزارشات",7),("🧾 صورت‌وضعیت",6)]:
            b=QPushButton(label); b.setMinimumHeight(40)
            if on_open_page: b.clicked.connect(lambda _=False,i=idx: on_open_page(i))
            rv.addWidget(b)
        rv.addStretch(); body.addWidget(left,3); body.addWidget(right,1); root.addLayout(body,1)
        self.refresh()
    def refresh(self):
        projects=self.service.store.list()
        while self.cards.count():
            item=self.cards.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        cards=[("پروژه‌ها",str(len(projects)),"پروژه ذخیره‌شده روی سیستم"),("سال‌های فهرست‌بها",str(len(self.catalog.years())),"داده‌های قابل انتخاب"),("وضعیت متره","فعال","PDF / DXF / DWG / IFC"),("حالت اجرا","آفلاین","داده‌ها محلی نگهداری می‌شوند")]
        for i,(a,b,c) in enumerate(cards): self.cards.addWidget(_card(a,b,c),0,i)
        self.table.setRowCount(0)
        for i,p in enumerate(projects[-8:][::-1]):
            self.table.insertRow(i)
            for j,val in enumerate([p.get("id",""),p.get("name",""),"آماده"]): self.table.setItem(i,j,QTableWidgetItem(str(val)))
