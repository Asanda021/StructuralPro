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
            b=QPushButton(label); b.setMinimumHeight(40); b.setObjectName("SecondaryAction")
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
            try:
                dash=self.service.financial_dashboard(p.get("id",""))
                status=f'دوره {dash["latest_statement_no"]} | پیشرفت {dash["progress_percent"]:.1f}%'
            except Exception:
                status="آماده"
            for j,val in enumerate([p.get("id",""),p.get("name",""),status]): self.table.setItem(i,j,QTableWidgetItem(str(val)))
        if projects:
            self.refresh_financial(projects[-1].get("id",""))
    def show_cost_control(self, project_id):
        try:
            control=self.service.project_financial_control(project_id)
        except Exception:
            return
        cards=[
            ("ارزش کارکرد",f'{control["earned_value"]:,.0f}',"کارکرد تجمعی"),
            ("انحراف هزینه",f'{control["cost_variance"]:,.0f}',"کارکرد منهای هزینه واقعی"),
            ("انحراف برنامه",f'{control["schedule_variance"]:,.0f}',"مقایسه با برنامه"),
            ("شاخص هزینه",("—" if control["cost_performance_index"] is None else f'{control["cost_performance_index"]:.2f}'),"CPI"),
        ]
        for i,(a,b,h) in enumerate(cards):
            self.cards.addWidget(_card(a,b,h),1,i)

    def refresh_financial(self, project_id):
        try:
            d=self.service.financial_dashboard(project_id)
        except Exception:
            return
        cards=[
            ("قرارداد / برآورد",f'{d["contract_amount"]:,.0f}',f'مبلغ پایه: {d["base_amount"]:,.0f}'),
            ("کارکرد تجمعی",f'{d["cumulative_work"]:,.0f}',f'پیشرفت: {d["progress_percent"]:.1f}%'),
            ("مانده قرارداد",f'{d["remaining_contract"]:,.0f}',f'{d["line_count"]} ردیف BOQ'),
            ("صورت‌وضعیت",str(d["statement_count"]),f'آخرین دوره: {d["latest_statement_no"] or "—"}'),
            ("قابل پرداخت تجمعی",f'{d["total_payable"]:,.0f}',f'آخرین دوره: {d["latest_payable"]:,.0f}'),
        ]
        while self.cards.count():
            item=self.cards.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i,(a,b,c) in enumerate(cards):
            self.cards.addWidget(_card(a,b,c),0,i)
