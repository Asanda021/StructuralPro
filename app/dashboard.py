"""Commercial dashboard widgets for StructuralPro Windows UI."""
from __future__ import annotations
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QFrame,QTableWidget,QTableWidgetItem,QHeaderView,QComboBox,QDoubleSpinBox,QLineEdit,QFileDialog

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
        self.alerts=QLabel("کنترل مالی: برای مشاهده هشدارها، پروژه و تاریخ مبنا را انتخاب کنید."); self.alerts.setObjectName("DashboardCard"); self.alerts.setWordWrap(True); root.addWidget(self.alerts)
        self.kpi_summary=QLabel("شاخص‌های مالی پروژه پس از انتخاب پروژه نمایش داده می‌شوند."); self.kpi_summary.setObjectName("DashboardCard"); self.kpi_summary.setWordWrap(True); root.addWidget(self.kpi_summary)
        self.integrity_summary=QLabel("کنترل صحت داده‌های مالی: آماده بررسی"); self.integrity_summary.setObjectName("DashboardCard"); self.integrity_summary.setWordWrap(True); root.addWidget(self.integrity_summary)
        self.activity_summary=QLabel("فعالیت پروژه: آماده"); self.activity_summary.setObjectName("DashboardCard"); self.activity_summary.setWordWrap(True); root.addWidget(self.activity_summary)
        control=QFrame(); control.setObjectName("DashboardCard"); cv=QHBoxLayout(control); cv.setContentsMargins(12,10,12,10)
        cv.addWidget(QLabel("کنترل مالی"))
        self.control_project=QComboBox(); self.control_project.setMinimumWidth(180)
        self.planned_cost=QDoubleSpinBox(); self.planned_cost.setMaximum(999999999999999.0); self.planned_cost.setDecimals(2); self.planned_cost.setPrefix("برنامه: ")
        self.actual_cost=QDoubleSpinBox(); self.actual_cost.setMaximum(999999999999999.0); self.actual_cost.setDecimals(2); self.actual_cost.setPrefix("واقعی: ")
        self.control_button=QPushButton("محاسبه کنترل"); self.control_button.setObjectName("PrimaryAction")
        self.control_result=QLabel("برای محاسبه، پروژه و هزینه‌های برنامه‌ای/واقعی را انتخاب کنید."); self.control_result.setWordWrap(True)
        cv.addWidget(self.control_project); cv.addWidget(self.planned_cost); cv.addWidget(self.actual_cost); cv.addWidget(self.control_button); cv.addWidget(self.control_result,2)
        root.addWidget(control)
        commitments=QFrame(); cv=QHBoxLayout(commitments); cv.setContentsMargins(12,10,12,10)
        cv.addWidget(QLabel("ثبت تعهد هزینه"))
        self.commit_amount=QDoubleSpinBox(); self.commit_amount.setMaximum(999999999999999.0); self.commit_amount.setDecimals(2)
        self.commit_desc=QLineEdit(); self.commit_desc.setPlaceholderText("شرح تعهد")
        self.commit_ref=QLineEdit(); self.commit_ref.setPlaceholderText("شماره مرجع")
        self.commit_date=QLineEdit(); self.commit_date.setPlaceholderText("تاریخ")
        self.commit_due=QLineEdit(); self.commit_due.setPlaceholderText("سررسید")
        self.commit_counterparty=QComboBox(); self.commit_counterparty.setPlaceholderText("طرف حساب")
        self.commit_button=QPushButton("ثبت تعهد"); self.commit_button.setObjectName("SecondaryAction")
        self.commit_summary=QLabel("تعهدات: ۰"); self.commit_summary.setWordWrap(True)
        for x in (self.commit_amount,self.commit_desc,self.commit_ref,self.commit_date,self.commit_due,self.commit_counterparty,self.commit_button,self.commit_summary): cv.addWidget(x)
        root.addWidget(commitments)
        receipts=QFrame(); rvh=QHBoxLayout(receipts); rvh.setContentsMargins(12,10,12,10)
        rvh.addWidget(QLabel("ثبت دریافتی"))
        self.receipt_amount=QDoubleSpinBox(); self.receipt_amount.setMaximum(999999999999999.0); self.receipt_amount.setDecimals(2)
        self.receipt_desc=QLineEdit(); self.receipt_desc.setPlaceholderText("شرح دریافتی")
        self.receipt_ref=QLineEdit(); self.receipt_ref.setPlaceholderText("شماره مرجع")
        self.receipt_date=QLineEdit(); self.receipt_date.setPlaceholderText("تاریخ")
        self.receipt_counterparty=QComboBox(); self.receipt_counterparty.setPlaceholderText("طرف حساب")
        self.receipt_button=QPushButton("ثبت دریافتی"); self.receipt_button.setObjectName("SecondaryAction")
        self.receipt_summary=QLabel("دریافتی: ۰"); self.receipt_summary.setWordWrap(True)
        for x in (self.receipt_amount,self.receipt_desc,self.receipt_ref,self.receipt_date,self.receipt_counterparty,self.receipt_button,self.receipt_summary): rvh.addWidget(x)
        root.addWidget(receipts)
        documents=QFrame(); dv=QHBoxLayout(documents); dv.setContentsMargins(12,10,12,10)
        dv.addWidget(QLabel("مرکز اسناد مالی"))
        self.document_number=QLineEdit(); self.document_number.setPlaceholderText("شماره سند / فاکتور")
        self.document_type=QLineEdit(); self.document_type.setPlaceholderText("نوع سند")
        self.document_counterparty=QComboBox(); self.document_counterparty.setPlaceholderText("طرف حساب")
        self.document_amount=QDoubleSpinBox(); self.document_amount.setMaximum(999999999999999.0); self.document_amount.setDecimals(2)
        self.document_date=QLineEdit(); self.document_date.setPlaceholderText("تاریخ")
        self.document_due=QLineEdit(); self.document_due.setPlaceholderText("سررسید")
        self.document_status=QComboBox(); self.document_status.addItem("پرداخت‌نشده","unpaid"); self.document_status.addItem("بخشی","partial"); self.document_status.addItem("پرداخت‌شده","paid")
        self.document_commitment=QLineEdit(); self.document_commitment.setPlaceholderText("شناسه تعهد")
        self.document_cost=QLineEdit(); self.document_cost.setPlaceholderText("شناسه هزینه")
        self.document_receipt=QLineEdit(); self.document_receipt.setPlaceholderText("شناسه دریافتی")
        self.document_button=QPushButton("ثبت سند"); self.document_button.setObjectName("SecondaryAction")
        self.document_summary=QLabel("اسناد: ۰"); self.document_summary.setWordWrap(True)
        self.counterparty_summary=QLabel("طرف حساب‌ها: ۰"); self.counterparty_summary.setWordWrap(True)
        for x in (self.document_number,self.document_type,self.document_counterparty,self.document_amount,self.document_date,self.document_due,self.document_status,self.document_commitment,self.document_cost,self.document_receipt,self.document_button,self.document_summary,self.counterparty_summary): dv.addWidget(x)
        root.addWidget(documents)
        aging=QFrame(); aging.setObjectName("DashboardCard"); av=QVBoxLayout(aging); av.setContentsMargins(12,10,12,10)
        ah=QHBoxLayout()
        ah.addWidget(QLabel("کنترل سررسید مالی"))
        self.aging_as_of=QLineEdit(); self.aging_as_of.setPlaceholderText("تاریخ مبنا؛ مثال ۱۴۰۵/۰۷/۱۰"); self.aging_as_of.setMinimumWidth(180)
        self.aging_button=QPushButton("بررسی سررسید"); self.aging_button.setObjectName("SecondaryAction")
        self.aging_export_button=QPushButton("خروجی"); self.aging_export_button.setObjectName("SecondaryAction")
        self.reconcile_button=QPushButton("تطبیق اسناد"); self.reconcile_button.setObjectName("SecondaryAction")
        self.reconcile_summary=QLabel("برای کنترل تطبیق وضعیت اسناد با پرداخت‌ها و دریافتی‌های لینک‌شده، این گزینه را اجرا کنید."); self.reconcile_summary.setWordWrap(True)
        self.reconcile_export_button=QPushButton("خروجی تطبیق"); self.reconcile_export_button.setObjectName("SecondaryAction")
        self.control_export_button=QPushButton("گزارش کنترل مالی"); self.control_export_button.setObjectName("SecondaryAction")
        self.statement_export_button=QPushButton("خلاصه صورت‌وضعیت"); self.statement_export_button.setObjectName("SecondaryAction")
        ah.addWidget(self.reconcile_export_button); ah.addWidget(self.control_export_button); ah.addWidget(self.statement_export_button)
        self.aging_summary=QLabel("برای مشاهده وضعیت سررسید، تاریخ مبنا را وارد کنید."); self.aging_summary.setWordWrap(True)
        ah.addWidget(self.aging_as_of); ah.addWidget(self.aging_button); ah.addWidget(self.aging_export_button); ah.addWidget(self.reconcile_button); ah.addWidget(self.aging_summary,2); av.addLayout(ah)
        av.addWidget(self.reconcile_summary)
        self.reconcile_table=QTableWidget(0,7)
        self.reconcile_table.setHorizontalHeaderLabels(["سند","شماره","ثبت‌شده","محاسباتی","تطبیق","اتصال","تسویه"])
        self.reconcile_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.reconcile_table.setAlternatingRowColors(True); av.addWidget(self.reconcile_table)
        self.aging_table=QTableWidget(0,7); self.aging_table.setHorizontalHeaderLabels(["نوع","شناسه","طرف حساب","مرجع","سررسید","وضعیت","مانده"])
        self.aging_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.aging_table.setAlternatingRowColors(True)
        av.addWidget(self.aging_table)
        root.addWidget(aging)
        parties=QFrame(); parties.setObjectName("DashboardCard"); pv=QVBoxLayout(parties); pv.setContentsMargins(12,10,12,10)
        ph=QHBoxLayout(); ph.addWidget(QLabel("دفتر طرف حساب‌ها"))
        self.party_name=QLineEdit(); self.party_name.setPlaceholderText("نام طرف حساب")
        self.party_role=QLineEdit(); self.party_role.setPlaceholderText("نقش: پیمانکار / فروشنده / کارفرما")
        self.party_button=QPushButton("ثبت طرف حساب"); self.party_button.setObjectName("SecondaryAction")
        self.party_update_button=QPushButton("ویرایش انتخاب‌شده"); self.party_update_button.setObjectName("SecondaryAction")
        self.party_toggle_button=QPushButton("فعال/غیرفعال"); self.party_toggle_button.setObjectName("SecondaryAction")
        self.party_export_button=QPushButton("خروجی طرف حساب‌ها"); self.party_export_button.setObjectName("SecondaryAction")
        self.party_rollup_button=QPushButton("رول‌آپ مالی"); self.party_rollup_button.setObjectName("SecondaryAction")
        self.party_ledger_button=QPushButton("گردش انتخاب‌شده"); self.party_ledger_button.setObjectName("SecondaryAction")
        self.party_summary=QLabel("طرف حساب‌های ثبت‌شده: ۰"); self.party_summary.setWordWrap(True)
        ph.addWidget(self.party_name,2); ph.addWidget(self.party_role,1); ph.addWidget(self.party_button); ph.addWidget(self.party_update_button); ph.addWidget(self.party_toggle_button); ph.addWidget(self.party_export_button); ph.addWidget(self.party_rollup_button); ph.addWidget(self.party_ledger_button); ph.addWidget(self.party_summary,2)
        pv.addLayout(ph)
        self.party_table=QTableWidget(0,4); self.party_table.setHorizontalHeaderLabels(["شناسه","نام","نقش","وضعیت"])
        self.party_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.party_table.setAlternatingRowColors(True)
        pv.addWidget(self.party_table)
        root.addWidget(parties)
        ledger=QFrame(); ledger.setObjectName("DashboardCard"); lv2=QHBoxLayout(ledger); lv2.setContentsMargins(12,10,12,10)
        lv2.addWidget(QLabel("ثبت هزینه"))
        self.cost_category=QComboBox(); self.cost_category.addItems(["مصالح","دستمزد","پیمانکار","تجهیزات","سایر"])
        self.cost_amount=QDoubleSpinBox(); self.cost_amount.setMaximum(999999999999999.0); self.cost_amount.setDecimals(2)
        self.cost_desc=QLineEdit(); self.cost_desc.setPlaceholderText("شرح هزینه")
        self.cost_date=QLineEdit(); self.cost_date.setPlaceholderText("تاریخ")
        self.cost_counterparty=QComboBox(); self.cost_counterparty.setPlaceholderText("طرف حساب")
        self.cost_button=QPushButton("ثبت هزینه"); self.cost_button.setObjectName("SecondaryAction")
        self.cost_summary=QLabel("دفتر هزینه: ۰"); self.cost_summary.setWordWrap(True)
        lv2.addWidget(self.cost_category); lv2.addWidget(self.cost_amount); lv2.addWidget(self.cost_desc,2); lv2.addWidget(self.cost_date); lv2.addWidget(self.cost_counterparty); lv2.addWidget(self.cost_button); lv2.addWidget(self.cost_summary,1)
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
        self.receipt_button.clicked.connect(self.add_receipt)
        self.commit_button.clicked.connect(self.add_commitment)
        self.document_button.clicked.connect(self.add_financial_document)
        self.document_button.clicked.connect(self.refresh_financial_document_status)
        self.aging_button.clicked.connect(self.refresh_aging)
        self.aging_button.clicked.connect(self.refresh_due_summary)
        self.aging_export_button.clicked.connect(self.export_aging)
        self.reconcile_button.clicked.connect(self.refresh_reconciliation)
        self.party_button.clicked.connect(self.add_counterparty)
        self.party_update_button.clicked.connect(self.update_counterparty)
        self.party_toggle_button.clicked.connect(self.toggle_counterparty)
        self.party_export_button.clicked.connect(self.export_counterparties)
        self.party_rollup_button.clicked.connect(self.export_counterparty_rollup)
        self.party_ledger_button.clicked.connect(self.export_selected_counterparty_ledger)
        self.reconcile_export_button.clicked.connect(self.export_reconciliation)
        self.control_export_button.clicked.connect(self.export_financial_control)
        self.statement_export_button.clicked.connect(self.export_statement_summary)
        self.party_table.itemSelectionChanged.connect(self.load_selected_counterparty)
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
            try: self.refresh_alerts(projects[-1].get("id",""))
            except Exception: pass
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
    def add_financial_document(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.document_summary.setText("پروژه‌ای انتخاب نشده است."); return
        def optional_id(widget):
            value=widget.text().strip()
            return int(value) if value else None
        try:
            self.service.add_project_financial_document(
                project_id,
                self.document_number.text(),
                self.document_type.text() or "سند مالی",
                float(self.document_amount.value()),
                counterparty=self._selected_counterparty_name(self.document_counterparty),
                date=self.document_date.text(),
                due_date=self.document_due.text(),
                payment_status=self.document_status.currentData(),
                commitment_id=optional_id(self.document_commitment),
                cost_entry_id=optional_id(self.document_cost),
                receipt_id=optional_id(self.document_receipt),
            )
            summary=self.service.project_financial_document_summary(project_id)
            self.document_summary.setText(f'اسناد: {summary["document_count"]} مورد | مجموع: {summary["document_total"]:,.0f} | پرداخت‌نشده: {summary["by_payment_status"]["unpaid"]:,.0f}')
            self.document_number.clear(); self.document_counterparty.setCurrentIndex(0); self.document_commitment.clear(); self.document_cost.clear(); self.document_receipt.clear()
        except Exception as exc:
            self.document_summary.setText(f"خطای ثبت سند: {exc}")

    def _selected_counterparty_name(self, widget):
        project_id=self.control_project.currentData()
        value=widget.currentData()
        if not project_id or not value:
            return ""
        item=self.service.find_project_counterparty_by_id(project_id, value)
        return item.get("name","") if item else ""

    def add_commitment(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.commit_summary.setText("پروژه‌ای انتخاب نشده است."); return
        try:
            self.service.add_project_commitment(project_id,float(self.commit_amount.value()),description=self.commit_desc.text(),date=self.commit_date.text(),due_date=self.commit_due.text(),reference=self.commit_ref.text(),counterparty=self._selected_counterparty_name(self.commit_counterparty))
            self.on_control_project_changed(self.control_project.currentIndex())
            self.commit_desc.clear(); self.commit_ref.clear()
        except Exception as exc:
            self.commit_summary.setText(f"خطای ثبت تعهد: {exc}")

    def add_receipt(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.receipt_summary.setText("پروژه‌ای انتخاب نشده است."); return
        try:
            self.service.add_project_receipt(project_id,float(self.receipt_amount.value()),description=self.receipt_desc.text(),date=self.receipt_date.text(),reference=self.receipt_ref.text(),counterparty=self._selected_counterparty_name(self.receipt_counterparty))
            self.on_control_project_changed(self.control_project.currentIndex())
            self.receipt_desc.clear(); self.receipt_ref.clear()
        except Exception as exc:
            self.receipt_summary.setText(f"خطای ثبت دریافتی: {exc}")

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
            pos=self.service.project_financial_position(project_id)
            self.commit_summary.setText(f'تعهدات: {pos["committed_cost"]:,.0f} | پرداخت‌نشده: {pos["unpaid_commitments"]:,.0f} | مواجهه نقدی: {pos["cash_exposure"]:,.0f} | {pos["commitment_count"]} ثبت')
            self.receipt_summary.setText(f'دریافتی: {pos["received"]:,.0f} | مطالبات: {pos["receivable"]:,.0f} | {pos["receipt_count"]} ثبت')
            ds=self.service.project_financial_document_summary(project_id)
            self.document_summary.setText(f'اسناد: {ds["document_count"]} مورد | مجموع: {ds["document_total"]:,.0f} | پرداخت‌نشده: {ds["by_payment_status"]["unpaid"]:,.0f}')
            self.refresh_counterparties(project_id)
            self.refresh_financial_document_status()
            self.refresh_financial_kpis(project_id)
            self.refresh_financial_controls(project_id)
            cp=self.service.project_counterparty_summary(project_id)
            self.counterparty_summary.setText(f'طرف حساب‌ها: {cp["counterparty_count"]} | ' + " | ".join(f'{x["counterparty"]}: {x["committed_amount"] + x["document_amount"]:,.0f}' for x in cp["counterparties"][:3]))
            self.control_result.setText(
                f'ارزش کارکرد: {d["cumulative_work"]:,.0f} | '
                f'هزینه واقعی: {d["actual_cost"]:,.0f} | '
                f'حاشیه کارکرد: {d["gross_margin"]:,.0f} | '
                f'پیشرفت: {d["progress_percent"]:.1f}%'
            )
        except Exception as exc:
            self.control_result.setText(f"خطای داشبورد مالی: {exc}")

    def refresh_alerts(self, project_id):
        as_of=self.aging_as_of.text().strip()
        if not as_of:
            self.alerts.setText("کنترل مالی: تاریخ مبنا را در بخش کنترل سررسید وارد کنید."); return
        try:
            a=self.service.project_financial_alerts(project_id, as_of); parts=[]
            if a["has_overdue"]: parts.append(f"⚠️ معوق: {a["overdue_count"]} مورد / {a["overdue_amount"]:,.0f}")
            if a["has_due_today"]: parts.append(f"🔔 سررسید امروز: {a["due_today_count"]} مورد")
            if a["has_missing_due_date"]: parts.append(f"📝 بدون سررسید: {a["no_due_date_count"]} مورد")
            self.alerts.setText(" | ".join(parts) if parts else "✅ هشدار مالی فعالی وجود ندارد.")
        except Exception as exc: self.alerts.setText(f"خطای کنترل هشدار مالی: {exc}")

    def refresh_financial_document_status(self):
        project_id=self.control_project.currentData()
        if not project_id:
            return
        try:
            s=self.service.project_financial_document_status_summary(project_id)
            self.document_summary.setText(
                f'اسناد: {s["document_count"]} | پرداخت‌نشده: {s["counts"]["unpaid"]} '
                f'| جزئی: {s["counts"]["partial"]} | پرداخت‌شده: {s["counts"]["paid"]} '
                f'| مغایرت: {s["mismatch_count"]}'
            )
        except Exception as exc:
            self.document_summary.setText(f"خطای خلاصه اسناد: {exc}")

    def refresh_due_summary(self):
        project_id=self.control_project.currentData()
        as_of=self.aging_as_of.text().strip()
        if not project_id or not as_of:
            return
        try:
            s=self.service.project_financial_due_summary(project_id,as_of)
            risk="—"
            if s["highest_risk"]:
                risk=f'{s["highest_risk"].get("source","")} #{s["highest_risk"].get("id","")}'
            self.aging_summary.setText(
                f'معوق: {s["overdue_count"]} / {s["overdue_amount"]:,.0f} | '
                f'امروز: {s["due_today_count"]} | آتی: {s["upcoming_count"]} | '
                f'بدون سررسید: {s["no_due_date_count"]} | مانده باز: {s["total_open_amount"]:,.0f} | ریسک اول: {risk}'
            )
        except Exception as exc:
            self.aging_summary.setText(f"خطای خلاصه سررسید: {exc}")

    def refresh_aging(self):
        project_id=self.control_project.currentData()
        as_of=self.aging_as_of.text().strip()
        if not project_id:
            self.aging_summary.setText("پروژه‌ای انتخاب نشده است."); return
        if not as_of:
            self.aging_summary.setText("تاریخ مبنا را وارد کنید."); return
        try:
            self.refresh_alerts(project_id)
            aging=self.service.project_financial_aging(project_id, as_of)
            self.aging_table.setRowCount(0)
            for i,row in enumerate(aging["rows"]):
                self.aging_table.insertRow(i)
                values=[row["source"],row["id"],row["counterparty"],row["reference"],row["due_date"],row["status"],"" if row["outstanding"] is None else f'{row["outstanding"]:,.0f}']
                for j,value in enumerate(values): self.aging_table.setItem(i,j,QTableWidgetItem(str(value)))
            self.aging_summary.setText(
                f'معوق: {aging["overdue_count"]} مورد | مبلغ معوق: {aging["overdue_amount"]:,.0f} | '
                f'سررسید امروز: {aging["due_today_count"]} | آتی: {aging["upcoming_count"]} | بدون سررسید: {aging["no_due_date_count"]}'
            )
        except Exception as exc:
            self.aging_summary.setText(f"خطای کنترل سررسید: {exc}")

    def add_counterparty(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.party_summary.setText("پروژه‌ای انتخاب نشده است."); return
        try:
            self.service.add_project_counterparty(project_id,self.party_name.text(),role=self.party_role.text())
            self.refresh_counterparties(project_id)
            self.party_name.clear(); self.party_role.clear()
        except Exception as exc:
            self.party_summary.setText(f"خطای ثبت طرف حساب: {exc}")

    def refresh_counterparties(self, project_id):
        try:
            parties=self.service.project_counterparties(project_id, active_only=True)
            preview=" | ".join(f'{x["name"]} ({x["role"] or "بدون نقش"})' for x in parties[:4])
            all_parties=self.service.project_counterparties(project_id)
            self.party_summary.setText(f"فعال: {len(parties)} | کل: {len(all_parties)}" + (f" | {preview}" if preview else ""))
            self.party_table.setRowCount(0)
            for i,item in enumerate(all_parties):
                self.party_table.insertRow(i)
                values=[item.get("id",""),item.get("name",""),item.get("role","") or "بدون نقش","فعال" if item.get("active",True) else "غیرفعال"]
                for j,value in enumerate(values): self.party_table.setItem(i,j,QTableWidgetItem(str(value)))
            for widget in (self.commit_counterparty,self.receipt_counterparty,self.document_counterparty,self.cost_counterparty):
                current=widget.currentData()
                widget.blockSignals(True); widget.clear(); widget.addItem("بدون طرف حساب","")
                for item in parties: widget.addItem(f'{item["name"]} — {item["role"] or "بدون نقش"}',item["id"])
                idx=widget.findData(current)
                widget.setCurrentIndex(idx if idx >= 0 else 0); widget.blockSignals(False)
        except Exception as exc:
            self.party_summary.setText(f"خطای دفتر طرف حساب‌ها: {exc}")
        except Exception as exc:
            self.party_summary.setText(f"خطای دفتر طرف حساب‌ها: {exc}")


    def load_selected_counterparty(self):
        row=self.party_table.currentRow()
        if row < 0:
            return
        item=self.party_table.item(row,0)
        if not item:
            return
        record=self.service.find_project_counterparty_by_id(self.control_project.currentData(), item.text())
        if record:
            self.party_name.setText(record.get("name",""))
            self.party_role.setText(record.get("role",""))

    def update_counterparty(self):
        project_id=self.control_project.currentData()
        row=self.party_table.currentRow()
        if not project_id or row < 0:
            self.party_summary.setText("یک طرف حساب را انتخاب کنید.")
            return
        item=self.party_table.item(row,0)
        if not item:
            return
        try:
            self.service.update_project_counterparty(project_id,item.text(),name=self.party_name.text(),role=self.party_role.text())
            self.refresh_counterparties(project_id)
        except Exception as exc:
            self.party_summary.setText(f"خطای ویرایش طرف حساب: {exc}")

    def toggle_counterparty(self):
        project_id=self.control_project.currentData()
        row=self.party_table.currentRow()
        if not project_id or row < 0:
            self.party_summary.setText("یک طرف حساب را انتخاب کنید.")
            return
        item=self.party_table.item(row,0)
        status=self.party_table.item(row,3)
        if not item or not status:
            return
        try:
            active=status.text() != "فعال"
            self.service.set_project_counterparty_active(project_id,item.text(),active)
            self.refresh_counterparties(project_id)
        except Exception as exc:
            self.party_summary.setText(f"خطای تغییر وضعیت طرف حساب: {exc}")

    def export_counterparties(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.party_summary.setText("پروژه‌ای انتخاب نشده است.")
            return
        path,_=QFileDialog.getSaveFileName(self,"ذخیره گزارش طرف حساب‌ها","","Excel (*.xlsx);;CSV (*.csv);;PDF (*.pdf);;Word (*.docx)")
        if not path:
            return
        try:
            suffix=path.rsplit(".",1)[-1].lower() if "." in path else "xlsx"
            self.service.project_counterparty_report(project_id,suffix,path)
            self.party_summary.setText(f"گزارش طرف حساب‌ها ذخیره شد: {path}")
        except Exception as exc:
            self.party_summary.setText(f"خطای خروجی طرف حساب‌ها: {exc}")

    def refresh_reconciliation(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.reconcile_summary.setText("پروژه‌ای انتخاب نشده است.")
            return
        try:
            r=self.service.project_financial_reconciliation(project_id)
            self.reconcile_table.setRowCount(0)
            for i,row in enumerate(r["rows"]):
                self.reconcile_table.insertRow(i)
                values=[row["document_id"],row["document_number"],row["manual_status"],row["derived_status"],
                        "تطبیق" if row["status_match"] else "بررسی",row["linkage_state"],f'{row["settlement_amount"]:,.0f}']
                for j,value in enumerate(values): self.reconcile_table.setItem(i,j,QTableWidgetItem(str(value)))
            self.reconcile_summary.setText(
                f'تطبیق اسناد: {r["matched_count"]} | نیازمند بررسی: {r["mismatch_count"]} | '
                f'بدون اتصال: {r["unlinked_count"]} | چند اتصال تسویه: {r["multiple_settlement_count"]}'
            )
        except Exception as exc:
            self.reconcile_summary.setText(f"خطای تطبیق اسناد: {exc}")

    def refresh_financial_controls(self, project_id):
        try:
            audit=self.service.project_financial_integrity_audit(project_id)
            self.integrity_summary.setText("کنترل صحت مالی: " + ("✅ بدون ایراد" if audit["healthy"] else f'⚠️ {audit["issue_count"]} ایراد'))
            act=self.service.project_activity_summary(project_id)
            self.activity_summary.setText(
                f'فعالیت پروژه | متره: {act["takeoffs"]} | ردیف BOQ: {act["boq_items"]} | '
                f'صورت‌وضعیت: {act["statement_periods"]} | اسناد: {act["documents"]} | '
                f'تعهدات: {act["commitments"]} | هزینه‌ها: {act["costs"]} | دریافتی: {act["receipts"]} | طرف حساب: {act["counterparties"]}'
            )
        except Exception as exc:
            self.integrity_summary.setText(f"خطای کنترل صحت: {exc}")

    def export_financial_control(self):
        project_id=self.control_project.currentData()
        if not project_id: return
        path,_=QFileDialog.getSaveFileName(self,"ذخیره گزارش کنترل مالی","","Excel (*.xlsx);;CSV (*.csv);;PDF (*.pdf);;Word (*.docx)")
        if not path: return
        try:
            suffix=path.rsplit(".",1)[-1].lower() if "." in path else "xlsx"
            self.service.project_financial_control_report(project_id,self.aging_as_of.text().strip(),suffix,path)
            self.integrity_summary.setText(f"گزارش کنترل مالی ذخیره شد: {path}")
        except Exception as exc:
            self.integrity_summary.setText(f"خطای خروجی کنترل مالی: {exc}")

    def export_statement_summary(self):
        project_id=self.control_project.currentData()
        if not project_id: return
        path,_=QFileDialog.getSaveFileName(self,"ذخیره خلاصه صورت‌وضعیت","","Excel (*.xlsx);;CSV (*.csv);;PDF (*.pdf);;Word (*.docx)")
        if not path: return
        try:
            suffix=path.rsplit(".",1)[-1].lower() if "." in path else "xlsx"
            self.service.project_statement_report(project_id,suffix,path)
            self.activity_summary.setText(f"خلاصه صورت‌وضعیت ذخیره شد: {path}")
        except Exception as exc:
            self.activity_summary.setText(f"خطای خروجی صورت‌وضعیت: {exc}")

    def refresh_financial_kpis(self, project_id):
        try:
            s=self.service.project_financial_kpi_summary(project_id, self.aging_as_of.text().strip())
            self.kpi_summary.setText(
                f'قرارداد: {s["contract_amount"]:,.0f} | کارکرد: {s["earned_value"]:,.0f} | '
                f'دریافتی: {s["received"]:,.0f} | مطالبات: {s["receivable"]:,.0f} | '
                f'تعهد باز: {s["unpaid_commitments"]:,.0f} | مواجهه نقدی: {s["cash_exposure"]:,.0f} | '
                f'معوق: {s["overdue_amount"]:,.0f} | مغایرت اسناد: {s["document_mismatches"]}'
            )
        except Exception as exc:
            self.kpi_summary.setText(f"خطای شاخص‌های مالی: {exc}")

    def export_reconciliation(self):
        project_id=self.control_project.currentData()
        if not project_id: return
        path,_=QFileDialog.getSaveFileName(self,"ذخیره گزارش تطبیق اسناد","","Excel (*.xlsx);;CSV (*.csv);;PDF (*.pdf);;Word (*.docx)")
        if not path: return
        try:
            suffix=path.rsplit(".",1)[-1].lower() if "." in path else "xlsx"
            self.service.project_financial_reconciliation_report(project_id,suffix,path)
            self.reconcile_summary.setText(f"گزارش تطبیق ذخیره شد: {path}")
        except Exception as exc:
            self.reconcile_summary.setText(f"خطای خروجی تطبیق: {exc}")

    def export_counterparty_rollup(self):
        project_id=self.control_project.currentData()
        if not project_id: return
        path,_=QFileDialog.getSaveFileName(self,"ذخیره رول‌آپ مالی","","Excel (*.xlsx);;CSV (*.csv);;PDF (*.pdf);;Word (*.docx)")
        if not path: return
        try:
            suffix=path.rsplit(".",1)[-1].lower() if "." in path else "xlsx"
            self.service.project_counterparty_financial_rollup_report(project_id,suffix,path)
            self.party_summary.setText(f"رول‌آپ مالی ذخیره شد: {path}")
        except Exception as exc:
            self.party_summary.setText(f"خطای خروجی رول‌آپ: {exc}")

    def export_selected_counterparty_ledger(self):
        project_id=self.control_project.currentData(); row=self.party_table.currentRow()
        if not project_id or row < 0: return
        item=self.party_table.item(row,0)
        if not item: return
        path,_=QFileDialog.getSaveFileName(self,"ذخیره گردش طرف حساب","","Excel (*.xlsx);;CSV (*.csv);;PDF (*.pdf);;Word (*.docx)")
        if not path: return
        try:
            party=self.service.find_project_counterparty_by_id(project_id,item.text())
            suffix=path.rsplit(".",1)[-1].lower() if "." in path else "xlsx"
            self.service.project_counterparty_ledger_by_id(project_id,item.text())
            self.service.project_counterparty_ledger_report(project_id,party["name"],suffix,path)
            self.party_summary.setText(f"گردش طرف حساب ذخیره شد: {path}")
        except Exception as exc:
            self.party_summary.setText(f"خطای خروجی گردش طرف حساب: {exc}")

    def export_aging(self):
        project_id=self.control_project.currentData()
        as_of=self.aging_as_of.text().strip()
        if not project_id or not as_of:
            self.aging_summary.setText("پروژه و تاریخ مبنا را مشخص کنید.")
            return
        path,_=QFileDialog.getSaveFileName(self,"ذخیره گزارش سررسید مالی","","Excel (*.xlsx);;CSV (*.csv);;PDF (*.pdf);;Word (*.docx)")
        if not path:
            return
        try:
            suffix=path.rsplit(".",1)[-1].lower() if "." in path else "xlsx"
            self.service.project_financial_aging_report(project_id,as_of,suffix,path)
            self.aging_summary.setText(f"گزارش سررسید ذخیره شد: {path}")
        except Exception as exc:
            self.aging_summary.setText(f"خطای خروجی سررسید: {exc}")

    def add_cost(self):
        project_id=self.control_project.currentData()
        if not project_id:
            self.cost_summary.setText("پروژه‌ای انتخاب نشده است.")
            return
        try:
            self.service.add_project_cost(
                project_id, self.cost_category.currentText(), float(self.cost_amount.value()),
                description=self.cost_desc.text(), date=self.cost_date.text(), counterparty=self._selected_counterparty_name(self.cost_counterparty)
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
            ("دریافتی",f'{self.service.project_receipt_summary(project_id)["total_received"]:,.0f}','جمع مبالغ دریافت‌شده'),
            ("مطالبات",f'{max(float(d["contract_amount"])-self.service.project_receipt_summary(project_id)["total_received"],0):,.0f}','قرارداد منهای دریافتی'),
            ("تعهدات",f'{self.service.project_commitment_summary(project_id)["committed_total"]:,.0f}','هزینه‌های تعهدشده'),
            ("پرداخت‌نشده",f'{self.service.project_commitment_summary(project_id)["unpaid_total"]:,.0f}','مانده تعهدات'),
            ("قابل پرداخت تجمعی",f'{d["total_payable"]:,.0f}',f'آخرین دوره: {d["latest_payable"]:,.0f}'),
        ]
        while self.cards.count():
            item=self.cards.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for i,(a,b,c) in enumerate(cards):
            self.cards.addWidget(_card(a,b,c),0,i)
