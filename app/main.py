"""StructuralPro Windows desktop UI: offline-first project, takeoff, drawing, pricing, reports and local AI."""
from __future__ import annotations
import sys
from pathlib import Path

def main()->int:
    try:
        from PySide6.QtWidgets import (
            QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,
            QLabel,QPushButton,QListWidget,QStackedWidget,QStatusBar,QLineEdit,
            QComboBox,QFormLayout,QMessageBox,QTextEdit,QFileDialog,QTableWidget,
            QTableWidgetItem,QHeaderView,QGroupBox
        )
        from PySide6.QtCore import Qt
        from core.platform.application import StructuralProApp
        from core.drawings.unified_takeoff import UnifiedDrawingTakeoff
        from core.pricing.catalog import PriceCatalog
        from core.ai.project_assistant import ProjectAssistant
        from core.reports.quality import prepare_rows
        from core.reports.project_report import build_report
    except ImportError as exc:
        print("StructuralPro dependencies are required:",exc); return 2

    app=QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setApplicationName("StructuralPro")
    service=StructuralProApp(Path.home()/".structuralpro")
    catalog=PriceCatalog()
    assistant=ProjectAssistant()
    w=QMainWindow(); w.setWindowTitle("StructuralPro — متره و برآورد حرفه‌ای"); w.resize(1500,920)

    root=QWidget(); layout=QHBoxLayout(root); nav=QVBoxLayout(); pages=QStackedWidget()
    title=QLabel("StructuralPro")
    title.setStyleSheet("font-size:24px;font-weight:700;padding:12px;")
    nav.addWidget(title)
    status=QLabel("🟢 آفلاین فعال | داده‌ها روی سیستم ذخیره می‌شوند")
    nav.addWidget(status)

    def page(name,desc):
        p=QWidget(); v=QVBoxLayout(p)
        h=QLabel(name); h.setStyleSheet("font-size:20px;font-weight:700;")
        v.addWidget(h); v.addWidget(QLabel(desc)); return p,v

    buttons=[]
    sections=["داشبورد","پروژه‌ها","متره سریع","متره از نقشه","فهرست‌بها","برآورد و BOQ","گزارشات","هوش مصنوعی آفلاین"]
    for name in sections:
        b=QPushButton(name); b.setMinimumHeight(46); buttons.append(b); nav.addWidget(b)

    # Dashboard
    p,v=page("داشبورد","نمای کلی پروژه و وضعیت موتورهای محلی")
    dash=QTextEdit(); dash.setReadOnly(True); v.addWidget(dash)
    def refresh_dash():
        projects=service.store.list()
        dash.setPlainText(
            f"تعداد پروژه‌ها: {len(projects)}\n"
            f"ذخیره‌سازی: SQLite محلی\n"
            f"متره: فعال\nنقشه: PDF / DXF / DWG / IFC\n"
            f"فهرست‌بها: {len(catalog.years())} سال بارگذاری‌شده\n"
            f"هوش مصنوعی: محلی و آفلاین\n\n"
            "اینترنت برای هسته نرم‌افزار الزامی نیست."
        )
    v.addWidget(QPushButton("بازخوانی داشبورد"))
    v.itemAt(v.count()-1).widget().clicked.connect(refresh_dash)
    pages.addWidget(p); idx_dash=pages.count()-1

    # Projects
    p,v=page("پروژه‌ها","ساخت، بازکردن و ذخیره پروژه‌ها")
    form=QFormLayout(); pid=QLineEdit(); pname=QLineEdit()
    form.addRow("شناسه پروژه:",pid); form.addRow("نام پروژه:",pname); v.addLayout(form)
    create=QPushButton("➕ ایجاد پروژه"); openb=QPushButton("📂 بازکردن پروژه"); plist=QListWidget(); pout=QLabel()
    v.addWidget(create); v.addWidget(openb); v.addWidget(plist); v.addWidget(pout)
    def refresh_projects():
        plist.clear()
        for x in service.store.list(): plist.addItem(f'{x["id"]} | {x["name"]}')
    def create_project():
        try:
            service.create_project(pname.text().strip() or "پروژه جدید",pid.text().strip() or "project")
            pout.setText("پروژه با موفقیت ذخیره شد."); refresh_projects(); refresh_dash()
        except Exception as e: QMessageBox.critical(w,"خطا",str(e))
    create.clicked.connect(create_project)
    def open_selected():
        if not plist.currentItem(): return
        selected=plist.currentItem().text().split(" | ",1)[0]; pid.setText(selected)
        project=service.open_project(selected)
        pout.setText(f'پروژه باز شد: {project.get("name","")}')
    openb.clicked.connect(open_selected)
    pages.addWidget(p); idx_projects=pages.count()-1

    # Quick takeoff
    p,v=page("متره سریع","ورود سریع مقادیر با فرم استاندارد")
    form=QFormLayout(); qpid=QLineEdit(); item=QComboBox(); item.addItems(["slab","wall","column","beam","footing_concrete"])
    length=QLineEdit(); width=QLineEdit(); height=QLineEdit(); price_code=QLineEdit()
    for x,l in ((qpid,"شناسه پروژه"),(item,"آیتم"),(length,"طول"),(width,"عرض"),(height,"ارتفاع"),(price_code,"کد فهرست‌بها")): form.addRow(l,x)
    v.addLayout(form); calc=QPushButton("محاسبه و ثبت"); out=QTextEdit(); out.setReadOnly(True); v.addWidget(calc); v.addWidget(out)
    def do_calc():
        try:
            params={"length":float(length.text() or 0),"width":float(width.text() or 0),"height":float(height.text() or 0),"member_code":item.currentText(),"price_code":price_code.text().strip() or None}
            row=service.add_takeoff(qpid.text().strip(),"building",item.currentText(),**params)
            out.setPlainText(f'ثبت شد\nمقدار: {row["quantities"][0]["amount"]} {row["quantities"][0]["unit"]}')
        except Exception as e: out.setPlainText("خطا: "+str(e))
    calc.clicked.connect(do_calc)
    pages.addWidget(p); idx_quick=pages.count()-1

    # Drawing takeoff
    p,v=page("متره از نقشه","ورود PDF/DWG/DXF/IFC و تولید کاندیدهای متره برای تأیید")
    file_edit=QLineEdit(); browse=QPushButton("انتخاب فایل"); inspect=QPushButton("🔎 بررسی نقشه"); dtable=QTableWidget(0,5)
    dtable.setHorizontalHeaderLabels(["تأیید","شرح","مقدار","واحد","منبع"]); dtable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    v.addWidget(file_edit); v.addWidget(browse); v.addWidget(inspect); v.addWidget(dtable)
    drawing_state={}
    browse.clicked.connect(lambda: file_edit.setText(QFileDialog.getOpenFileName(w,"انتخاب نقشه","","Plans (*.pdf *.dwg *.dxf *.ifc *.ifczip);;All files (*)")[0]))
    def inspect_drawing():
        try:
            drawing_state.clear(); drawing_state.update(UnifiedDrawingTakeoff().inspect(file_edit.text().strip()))
            dtable.setRowCount(0)
            for i,r in enumerate(drawing_state.get("candidates",[]) or [],1):
                dtable.insertRow(i-1); cb=QComboBox(); cb.addItems(["تأیید","رد"]); cb.setCurrentIndex(0 if r.get("needs_confirmation") else 0)
                dtable.setCellWidget(i-1,0,cb)
                vals=[r.get("description",""),r.get("quantity",""),r.get("unit",""),r.get("source",r.get("global_id",""))]
                for j,val in enumerate(vals,1): dtable.setItem(i-1,j,QTableWidgetItem(str(val)))
            if drawing_state.get("kind")=="cad": outmsg=f'نقشه CAD: {drawing_state["summary"]["entities"]} المان'
            else: outmsg=f'تعداد کاندیدها: {len(drawing_state.get("candidates",[]))}'
            status.setText("🟢 "+outmsg+" | قبل از ورود به BOQ تأیید کنید")
        except Exception as e: QMessageBox.critical(w,"خطای نقشه",str(e))
    inspect.clicked.connect(inspect_drawing)
    pages.addWidget(p); idx_drawing=pages.count()-1

    # Pricing
    p,v=page("فهرست‌بها","بارگذاری CSV، جستجو و کنترل داده‌های سالانه")
    pform=QHBoxLayout(); pyear=QLineEdit(); pquery=QLineEdit(); load=QPushButton("بارگذاری CSV"); search=QPushButton("جستجو")
    pform.addWidget(QLabel("سال:")); pform.addWidget(pyear); pform.addWidget(QLabel("عبارت:")); pform.addWidget(pquery); pform.addWidget(load); pform.addWidget(search); v.addLayout(pform)
    ptable=QTableWidget(0,6); ptable.setHorizontalHeaderLabels(["سال","کد","شرح","واحد","بهای واحد","فصل"]); ptable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); v.addWidget(ptable)
    def load_prices():
        path=QFileDialog.getOpenFileName(w,"CSV فهرست‌بها","","CSV (*.csv)")[0]
        if not path:return
        try:
            text=Path(path).read_text(encoding="utf-8-sig"); n=catalog.import_csv(text,replace_year=True); pquery.setText(""); search_prices(); status.setText(f"🟢 {n} ردیف فهرست‌بها بارگذاری شد")
        except Exception as e: QMessageBox.critical(w,"خطای فهرست‌بها",str(e))
    load.clicked.connect(load_prices)
    def search_prices():
        try: year=int(pyear.text()) if pyear.text().strip() else None
        except ValueError: year=None
        rows=catalog.search(pquery.text(),year=year,limit=100); ptable.setRowCount(0)
        for i,x in enumerate(rows):
            ptable.insertRow(i)
            for j,val in enumerate([x.year,x.code,x.description,x.unit,x.unit_price,x.chapter]): ptable.setItem(i,j,QTableWidgetItem(str(val)))
    search.clicked.connect(search_prices)
    pages.addWidget(p); idx_prices=pages.count()-1

    # BOQ
    p,v=page("برآورد و BOQ","جمع مقادیر و مبالغ پروژه")
    bpid=QLineEdit(); bgo=QPushButton("نمایش BOQ"); btable=QTableWidget(0,6); btable.setHorizontalHeaderLabels(["ردیف","شرح","مقدار","واحد","کد","مبلغ"]); btable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    v.addWidget(bpid); v.addWidget(bgo); v.addWidget(btable)
    def show_boq():
        project=service.open_project(bpid.text().strip())
        if not project: QMessageBox.warning(w,"پروژه","پروژه پیدا نشد."); return
        rows=project.get("boq",[]); btable.setRowCount(0)
        for i,r in enumerate(rows):
            btable.insertRow(i)
            vals=[r.get("item_no",i+1),r.get("description",""),r.get("quantity",0),r.get("unit",""),r.get("price_code",""),r.get("total","")]
            for j,val in enumerate(vals): btable.setItem(i,j,QTableWidgetItem(str(val)))
    bgo.clicked.connect(show_boq)
    pages.addWidget(p); idx_boq=pages.count()-1

    # Reports
    p,v=page("گزارشات","خروجی استاندارد پروژه با ستون‌های پایدار و قابل ارائه")
    rpid=QLineEdit(); rfmt=QComboBox(); rfmt.addItems(["xlsx","pdf","docx","csv"]); rgo=QPushButton("ساخت گزارش"); rout=QTextEdit(); rout.setReadOnly(True)
    v.addWidget(rpid); v.addWidget(rfmt); v.addWidget(rgo); v.addWidget(rout)
    def make_report():
        project=service.open_project(rpid.text().strip())
        if not project: QMessageBox.warning(w,"گزارش","پروژه پیدا نشد."); return
        rows=[{"source":"manual","price_code":q.get("price_code"),"description":q.get("title",""),"quantity":q.get("amount",0),"unit":q.get("unit",""),"unit_price":q.get("unit_price")} for t in project.get("takeoffs",[]) for q in t.get("quantities",[])]
        rows=prepare_rows(rows,"fa")
        path=QFileDialog.getSaveFileName(w,"ذخیره گزارش",f'{project.get("name","project")}.{rfmt.currentText()}',f'{rfmt.currentText().upper()} (*.{rfmt.currentText()})')[0]
        if not path:return
        try: build_report(project.get("name",""),rows,{"rtl":True}).export(path,rfmt.currentText()); rout.setPlainText("گزارش با موفقیت ساخته شد.\n"+path)
        except Exception as e: QMessageBox.critical(w,"خطای گزارش",str(e))
    rgo.clicked.connect(make_report)
    pages.addWidget(p); idx_reports=pages.count()-1

    # AI
    p,v=page("هوش مصنوعی آفلاین","بازبینی پروژه، هشدار داده‌های ناقص و مقایسه تغییرات")
    apid=QLineEdit(); ago=QPushButton("🤖 بازبینی پروژه"); aout=QTextEdit(); aout.setReadOnly(True)
    v.addWidget(apid); v.addWidget(ago); v.addWidget(aout)
    def review():
        project=service.open_project(apid.text().strip())
        if not project: QMessageBox.warning(w,"AI","پروژه پیدا نشد."); return
        r=assistant.review(project)
        text=r["text"]+"\n\n"+"\n".join(f'{x["severity"]}: {x["code"]}' for x in r["issues"]) if r["issues"] else r["text"]+"\n\nایراد داده‌ای پیدا نشد."
        aout.setPlainText(text)
    ago.clicked.connect(review)
    pages.addWidget(p); idx_ai=pages.count()-1

    # navigation
    for b,i in zip(buttons,range(pages.count())): b.clicked.connect(lambda checked=False,i=i: pages.setCurrentIndex(i))
    nav.addStretch()
    layout.addLayout(nav,1); layout.addWidget(pages,4); w.setCentralWidget(root)
    w.setStatusBar(QStatusBar()); w.statusBar().showMessage("StructuralPro آماده است — هسته آفلاین")
    refresh_projects(); refresh_dash(); pages.setCurrentIndex(idx_dash)
    w.show(); return app.exec()

if __name__=="__main__": raise SystemExit(main())
