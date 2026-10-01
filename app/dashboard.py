"""Commercial dashboard widgets for StructuralPro Windows UI."""
from __future__ import annotations
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QFrame,QTableWidget,QTableWidgetItem,QHeaderView,QComboBox,QDoubleSpinBox,QLineEdit

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
        control=QFrame(); control.setObjectName("DashboardCard"); cv=QHBoxLayout(control); cv.setContentsMargins(12,10,12,10)
        cv.addWidget(QLabel("کنترل مالی"))
        self.control_project=QComboBox(); self.control_project.setMinimumWidth(180)
        self.planned_cost=QDoubleSpinBox(); self.planned_cost.setMaximum(999999999999999.0); self.planned_cost.setDecimals(2); self.planned_cost.setPrefix("برنامه: ")
        self.actual_cost=QDoubleSpinBox(); self.actual_cost.setMaximum(999999999999999.0); self.actual_cost.setDecimals(2); self.actual_cost.setPrefix("واقعی: ")
        self.control_button=QPushButton("محاسبه کنترل"); self.control_button.setObjectName("PrimaryAction")
        self.control_result=QLabel("برای محاسبه، پروژه و هزینه‌های برنامه‌ای/واقعی را انتخاب کنید."); self.control_result.setWordWrap(True)
        cv.addWidget(self.control_project); cv.addWidget(self.planned_cost); cv.addWidget(self.actual_cost); cv.addWidget(self.control_button); cv.addWidget(self.control_result,2)
        root.addWidget(control)
        ledger=QFrame(); ledger.setObjectName("DashboardCard"); lv2=QHBoxLayout(ledger); lv2.setContentsMargins(12,10,12,10)
        lv2.addWidget(QLabel("ثبت هزینه"))
        self.cost_category=QComboBox(); self.cost_category.addItems(["مصالح","دستمزد","پیمانکار","تجهیزات","سایر"])
        self.cost_amount=QDoubleSpinBox(); self.cost_amount.setMaximum(999999999999999.0); self.cost_amount.setDecimals(2)
        self.cost_desc=QLineEdit(); self.cost_desc.setPlaceholderText("شرح هزینه")
        self.cost_date=QLineEdit(); self.cost_date.setPlaceholderText("تاریخ")
        self.cost_button=QPushButton("ثبت هزینه"); self.cost_button.setObjectName("SecondaryAction")
        self.cost_summary=QLabel("دفتر هزینه: ۰"); self.cost_summary.setWordWrap(True)
        lv2.addWidget(self.cost_category); lv2.addWidget(self.cost_amount); lv2.addWidget(self.cost_desc,2); lv2.addWidget(self.cost_date); lv2.addWidget(self.cost_button); lv2.addWidget(self.cost_summary,1)
        root.addWidget(ledger)
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
        self.control_button.clicked.connect(self.calculate_control)
        self.cost_button.clicked.connect(self.add_cost)
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
        self.control_project.blockSignals(True)
        self.control_project.clear()
        for p in projects: self.control_project.addItem(f'{p.get("id","")} | {p.get("name","")}', p.get("id",""))
        self.control_project.blockSignals(False)
        if not getattr(self, "_control_signal_connected", False):
            self.control_project.currentIndexChanged.connect(self.on_control_project_changed)
            self._control_signal_connected=True
        if projects:
            self.refresh_financial(projects[-1].get("id",""))
            try:
                s=self.service.project_cost_summary(projects[-1].get("id",""))
                self.cost_summary.setText(f'دفتر هزینه: {s["entry_count"]} مورد | مجموع: {s["actual_cost"]:,.0f}')
                self.actual_cost.setValue(float(s["actual_cost"]))
            except Exception:
                pass
            self.control_project.setCurrentIndex(self.control_project.count()-1)
            try:
                d=self.service.financial_dashboard(projects[-1].get("id",""))
                self.planned_cost.setValue(float(d["contract_amount"]))
            except Exception:
                pass
    def on_control_project_changed(self, _index):
        project_id=self.control_project.currentData()
        if not project_id:
            return
        try:
            d=self.service.financial_dashboard(project_id)
            self.refresh_financial(project_id)
            self.planned_cost.setValue(float(d["contract_amount"]))
            self.actual_cost.setValue(float(d["actual_cost"]))
            self.cost_summary.setText(f'دفتر هزینه: {d["cost_entry_count"]} مورد | مجموع: {d["actual_cost"]:,.0f}')
            self.control_result.setText(
                f'ارزش کارکرد: {d["cumulative_work"]:,.0f} | '
                f'هزینه واقعی: {d["actual_cost"]:,.0f} | '
                f'حاشیه کارکرد: {d["gross_margin"]:,.0f} | '
                f'پیشرفت: {d["progress_percent"]:.1f}%'
            )
        except Exception as exc:
            self.control_result.setText(f"خطای داشبورد مالی: {exc}")

    def add_cost(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.cost_summary.setText("پروژه‌ای انتخاب نشده است.")
            return
        try:
            self.service.add_project_cost(
                project_id, self.cost_category.currentText(), float(self.cost_amount.value()),
                description=self.cost_desc.text(), date=self.cost_date.text()
            )
            s=self.service.project_cost_summary(project_id)
            self.cost_summary.setText(f'دفتر هزینه: {s["entry_count"]} مورد | مجموع: {s["actual_cost"]:,.0f}')
            self.actual_cost.setValue(float(s["actual_cost"]))
            self.cost_desc.clear()
        except Exception as exc:
            self.cost_summary.setText(f"خطای ثبت هزینه: {exc}")

    def calculate_control(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.control_result.setText("پروژه‌ای برای کنترل مالی انتخاب نشده است.")
            return
        try:
            d=self.service.project_financial_control(
                project_id,
                planned_cost=float(self.planned_cost.value()),
                actual_cost=float(self.actual_cost.value()),
            )
            cpi=d["cost_performance_index"]
            cpi_text="—" if cpi is None else f'{cpi:.2f}'
            self.control_result.setText(
                f'ارزش کارکرد: {d["earned_value"]:,.0f} | '
                f'انحراف هزینه: {d["cost_variance"]:,.0f} | '
                f'انحراف برنامه: {d["schedule_variance"]:,.0f} | '
                f'CPI: {cpi_text} | پیشرفت: {d["progress_percent"]:.1f}%'
            )
        except Exception as exc:
            self.control_result.setText(f"خطای کنترل مالی: {exc}")

    def refresh_financial(self, project_id):
        try:
            d=self.service.financial_dashboard(project_id)
        except Exception:
            return
        cards=[
            ("قرارداد / برآورد",f'{d["contract_amount"]:,.0f}',f'مبلغ پایه: {d["base_amount"]:,.0f}'),
            ("کارکرد تجمعی",f'{d["cumulative_work"]:,.0f}',f'پیشرفت: {d["progress_percent"]:.1f}%'),
            ("مانده قرارداد",f'{d["remaining_contract"]:,.0f}',f'{d["line_count"]} ردیف BOQ'),
            ("هزینه واقعی",f'{d["actual_cost"]:,.0f}',f'{d["cost_entry_count"]} ثبت هزینه'),
            ("حاشیه کارکرد",f'{d["gross_margin"]:,.0f}','کارکرد منهای هزینه ثبت‌شده'),
            ("قابل پرداخت تجمعی",f'{d["total_payable"]:,.0f}',f'آخرین دوره: {d["latest_payable"]:,.0f}'),
        ]
        while self.cards.count():
            item=self.cards.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i,(a,b,c) in enumerate(cards):
            self.cards.addWidget(_card(a,b,c),0,i)
