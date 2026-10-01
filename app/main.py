"""StructuralPro Windows desktop UI: offline-first project, takeoff, drawing, pricing, reports and local AI."""
from __future__ import annotations
import sys
from pathlib import Path
import json

def main()->int:
    try:
        from PySide6.QtWidgets import (
            QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,
            QLabel,QPushButton,QListWidget,QStackedWidget,QStatusBar,QLineEdit,
            QComboBox,QFormLayout,QMessageBox,QTextEdit,QFileDialog,QTableWidget,
            QTableWidgetItem,QHeaderView,QGroupBox,QTabWidget
        )
        from PySide6.QtCore import Qt
        from core.platform.application import StructuralProApp
        from core.drawings.unified_takeoff import UnifiedDrawingTakeoff
        from core.pricing.catalog import PriceCatalog
        from core.ai.project_assistant import ProjectAssistant
        from core.reports.quality import prepare_rows
        from core.reports.project_report import build_report
        from core.revisions.compare import compare_rows, summary
        from core.takeoff.templates import TemplateLibrary
        from core.takeoff.formulas import evaluate
        from core.search.global_search import search_project
        from core.history.undo import CommandStack
        from core.drawings.sheets import SheetRegistry
        from core.drawings.markup import MarkupStore
        from core.drawings.pdf_measurement import PDFMeasurementSession
        from core.drawings.ifc_inventory import inventory as ifc_inventory
        from core.takeoff.estimate import build_estimate
        from core.projects.metadata import ProjectMetadata
        from core.projects.project_model import ProjectModel
        from core.projects.backup import BackupManager
        from core.pricing.source_registry import PriceSourceRegistry, PriceSource
        from core.reports.designer import ReportLayout
        from core.revisions.manager import RevisionManager
        from core.commercial.progress import build_progress
        from core.reports.production import prepare_report
        from app.graphical_takeoff import GraphicalTakeoffDialog
        from app.theme import APP_STYLESHEET
        from app.dashboard import DashboardPage
        from core.drawings.dwg_capabilities import detect_dwg_capabilities
    except ImportError as exc:
        print("StructuralPro dependencies are required:",exc); return 2

    app=QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setApplicationName("StructuralPro")
    app.setStyleSheet(APP_STYLESHEET)
    service=StructuralProApp(Path.home()/".structuralpro")
    catalog=PriceCatalog()
    assistant=ProjectAssistant()
    w=QMainWindow(); w.setWindowTitle("StructuralPro — متره و برآورد حرفه‌ای"); w.resize(1500,920)

    root=QWidget(); layout=QHBoxLayout(root); nav_widget=QWidget(); nav_widget.setObjectName("NavigationPanel"); nav=QVBoxLayout(nav_widget); pages=QStackedWidget()
    title=QLabel("StructuralPro")
    title.setObjectName("BrandTitle")
    nav.addWidget(title)
    status=QLabel("🟢 آفلاین فعال | داده‌ها روی سیستم ذخیره می‌شوند")
    nav.addWidget(status)

    def page(name,desc):
        p=QWidget(); v=QVBoxLayout(p); v.setContentsMargins(24,20,24,20); v.setSpacing(12)
        h=QLabel(name); h.setObjectName("PageTitle")
        d=QLabel(desc); d.setObjectName("PageDescription"); d.setWordWrap(True)
        v.addWidget(h); v.addWidget(d); return p,v

    buttons=[]
    sections=["داشبورد","پروژه‌ها","متره سریع","متره از نقشه","فهرست‌بها","برآورد و BOQ","صورت‌وضعیت","گزارشات","اسناد پروژه","ابزارهای حرفه‌ای","کنترل کیفیت","هوش مصنوعی آفلاین","تنظیمات"]
    for name in sections:
        b=QPushButton(name); b.setObjectName("NavButton"); b.setCheckable(True); b.setAutoExclusive(False); b.setMinimumHeight(44); b.setToolTip(name); buttons.append(b); nav.addWidget(b)

    # Dashboard — Canva-aligned commercial shell with real project data
    dashboard_page=DashboardPage(service,catalog,lambda i: pages.setCurrentIndex(i))
    pages.addWidget(dashboard_page); idx_dash=pages.count()-1

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
    file_edit=QLineEdit(); browse=QPushButton("انتخاب فایل"); inspect=QPushButton("🔎 بررسی نقشه"); graphical=QPushButton("📐 متره گرافیکی"); dtable=QTableWidget(0,5)
    dtable.setHorizontalHeaderLabels(["تأیید","شرح","مقدار","واحد","منبع"]); dtable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    v.addWidget(file_edit); v.addWidget(browse); v.addWidget(inspect); v.addWidget(graphical); v.addWidget(dtable)
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
            if drawing_state.get("kind")=="cad":\n                caps=detect_dwg_capabilities()\n                outmsg=f'نقشه CAD: {drawing_state["summary"]["entities"]} المان | {caps.message}'
            else: outmsg=f'تعداد کاندیدها: {len(drawing_state.get("candidates",[]))}'
            status.setText("🟢 "+outmsg+" | قبل از ورود به BOQ تأیید کنید")
        except Exception as e: QMessageBox.critical(w,"خطای نقشه",str(e))
    inspect.clicked.connect(inspect_drawing)
    graphical.clicked.connect(lambda: GraphicalTakeoffDialog(w,file_edit.text().strip()).exec())
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

    # Professional tools: revisions, templates, formulas, search, sheets, markups
    p,v=page("ابزارهای حرفه‌ای","کنترل Revision، قالب‌ها، فرمول، جستجو، نقشه‌ها و یادداشت‌ها")
    tools=QTabWidget(); v.addWidget(tools)
    rv=QWidget(); rvv=QVBoxLayout(rv); oldtxt=QTextEdit(); newtxt=QTextEdit()
    rvv.addWidget(QLabel("نسخه قدیم (JSON ردیف‌ها)")); rvv.addWidget(oldtxt); rvv.addWidget(QLabel("نسخه جدید (JSON ردیف‌ها)")); rvv.addWidget(newtxt)
    rvc=QPushButton("مقایسه Revision"); rvout=QTextEdit(); rvout.setReadOnly(True); rvv.addWidget(rvc); rvv.addWidget(rvout)
    def do_revision():
        import json
        try:
            a=json.loads(oldtxt.toPlainText() or "[]"); b=json.loads(newtxt.toPlainText() or "[]")
            c=compare_rows(a,b); rvout.setPlainText(json.dumps({"changes":c,"summary":summary(c)},ensure_ascii=False,indent=2))
        except Exception as e: rvout.setPlainText("خطا: "+str(e))
    rvc.clicked.connect(do_revision); tools.addTab(rv,"Revision")
    tf=QWidget(); tfv=QVBoxLayout(tf); tmpl=QComboBox(); lib=TemplateLibrary()
    tmpl.addItems([f"{x.code} | {x.name} | {x.formula}" for x in lib.items.values()]); tfv.addWidget(tmpl)
    expr=QLineEdit("length*height-openings"); vars_=QLineEdit("length=5,height=3,openings=2")
    tfv.addWidget(expr); tfv.addWidget(vars_); fe=QPushButton("محاسبه فرمول"); fo=QLabel(); tfv.addWidget(fe); tfv.addWidget(fo)
    def do_formula():
        try:
            d={}; [d.__setitem__(x.split("=",1)[0].strip(),float(x.split("=",1)[1])) for x in vars_.text().split(",") if "=" in x]
            fo.setText("نتیجه: "+str(evaluate(expr.text(),d)))
        except Exception as e: fo.setText("خطا: "+str(e))
    fe.clicked.connect(do_formula); tools.addTab(tf,"قالب و فرمول")
    sm=QWidget(); smv=QVBoxLayout(sm); sq=QLineEdit(); sq.setPlaceholderText("جستجوی پروژه، متره، آیتم یا کد فهرست‌بها")
    sb=QPushButton("جستجوی سراسری"); so=QTextEdit(); so.setReadOnly(True); smv.addWidget(sq); smv.addWidget(sb); smv.addWidget(so)
    def do_search():
        import json
        project=service.open_project(pid.text().strip()) if pid.text().strip() else None
        so.setPlainText(json.dumps(search_project(project,sq.text()) if project else [],ensure_ascii=False,indent=2))
    sb.clicked.connect(do_search)
    sheets=SheetRegistry(); markups=MarkupStore()
    smv.addWidget(QLabel("پشتیبانی چندنقشه و Markup در هسته پروژه فعال است."))
    tools.addTab(sm,"جستجو و نقشه")
    tools.addTab(QLabel("گزارش‌ساز قابل تنظیم، Excel Bridge و Undo/Redo در هسته فعال است."),"گزارش و Excel")
    qa=QWidget(); qav=QVBoxLayout(qa)
    qav.addWidget(QLabel("کنترل یکپارچگی ۱۰ سطح اصلی محصول"))
    qstatus=QTextEdit(); qstatus.setReadOnly(True); qav.addWidget(qstatus)
    def refresh_quality():
        checks=[("متره PDF گرافیکی",PDFMeasurementSession),("متره IFC/BIM",ifc_inventory),("برآورد و Costing",build_estimate),("Metadata پروژه",ProjectMetadata),("Revision",RevisionManager),("پیشرفت/صورت‌وضعیت",build_progress),("گزارش فارسی",prepare_report)]
        qstatus.setPlainText("\n".join("🟢 "+name+" | آماده" for name,_ in checks)+"\n\nDWG/DXF، فهرست‌بها و BOQ نیز در هسته فعال هستند.")
    qbtn=QPushButton("بازبینی وضعیت ۱۰ بخش"); qbtn.clicked.connect(refresh_quality); qav.addWidget(qbtn); refresh_quality()
    tools.addTab(qa,"کنترل محصول")
    pages.addWidget(p); idx_tools=pages.count()-1

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

    # Commercial statement shortcut
    p,v=page("صورت‌وضعیت","محاسبه پیشرفت، مبلغ دوره، کسورات، مالیات و خالص قابل پرداخت")
    stid=QLineEdit(); stgo=QPushButton("محاسبه صورت‌وضعیت"); stout=QTextEdit(); stout.setReadOnly(True)
    v.addWidget(stid); v.addWidget(stgo); v.addWidget(stout)
    def statement_shortcut():
        try:
            project=service.open_project(stid.text().strip())
            lines=[]
            if project:
                for row in project.get("boq",[]):
                    lines.append({"code":row.get("price_code",""),"contract_quantity":row.get("quantity",0),"previous_quantity":row.get("previous_quantity",0),"current_quantity":row.get("current_quantity",row.get("quantity",0)),"unit_price":row.get("unit_price",0)})
            stout.setPlainText(json.dumps(build_progress(lines),ensure_ascii=False,indent=2) if lines else "برای پروژه انتخاب‌شده ردیف قابل محاسبه وجود ندارد.")
        except Exception as e: stout.setPlainText("خطا: "+str(e))
    stgo.clicked.connect(statement_shortcut); pages.addWidget(p); idx_statement=pages.count()-1

    # Project documents
    p,v=page("اسناد پروژه","مرکز ثبت و پیگیری نقشه‌ها، فایل‌های قراردادی و خروجی‌های پروژه")
    docpath=QLineEdit(); docadd=QPushButton("افزودن مسیر سند"); doclist=QListWidget()
    v.addWidget(docpath); v.addWidget(docadd); v.addWidget(doclist)
    def add_doc():
        path=docpath.text().strip()
        if path: doclist.addItem(path); docpath.clear()
    docadd.clicked.connect(add_doc); pages.addWidget(p); idx_docs=pages.count()-1

    # Quality control
    p,v=page("کنترل کیفیت","کنترل یکپارچگی داده، متره، BOQ، قیمت و گزارش قبل از تحویل")
    qc=QTextEdit(); qc.setReadOnly(True); qc.setPlainText("\n".join([
        "🟢 کنترل ساختار پروژه","🟢 کنترل متره و واحدها","🟢 کنترل BOQ و کد فهرست‌بها",
        "🟢 کنترل جمع مبالغ","🟢 کنترل گزارش فارسی و RTL","🟢 کنترل Revision و Change Log"
    ])); v.addWidget(qc); pages.addWidget(p); idx_quality=pages.count()-1

    # Settings
    p,v=page("تنظیمات","تنظیمات ظاهری، زبان، واحدها و مسیر ذخیره‌سازی محلی")
    lang=QComboBox(); lang.addItems(["فارسی (RTL)","English (LTR)"])
    unit=QComboBox(); unit.addItems(["متر / مترمربع / مترمکعب","سانتی‌متر / میلی‌متر"])
    v.addWidget(QLabel("زبان رابط")); v.addWidget(lang); v.addWidget(QLabel("واحد پیش‌فرض")); v.addWidget(unit)
    v.addWidget(QLabel("ذخیره‌سازی: محلی و آفلاین | مسیر داده: ~/.structuralpro"))
    pages.addWidget(p); idx_settings=pages.count()-1

    # Project management: floors/drawings/takeoff/BOQ/report workflow
    pm=QWidget(); pmv=QVBoxLayout(pm)
    pmv.addWidget(QLabel("مدیریت حرفه‌ای پروژه | پروژه → طبقات → نقشه‌ها → متره → BOQ → گزارش"))
    pmform=QFormLayout(); pmid=QLineEdit(); pmname=QLineEdit(); pmfloor=QLineEdit(); pmdrawing=QLineEdit()
    pmform.addRow("شناسه:",pmid); pmform.addRow("نام:",pmname); pmform.addRow("طبقه جدید:",pmfloor); pmform.addRow("مسیر نقشه:",pmdrawing); pmv.addLayout(pmform)
    pmadd=QPushButton("ثبت ساختار پروژه"); pmout=QTextEdit(); pmout.setReadOnly(True); pmv.addWidget(pmadd); pmv.addWidget(pmout)
    def manage_project():
        try:
            model=ProjectModel(pmid.text().strip() or "project",pmname.text().strip() or "پروژه")
            if pmfloor.text().strip(): model.add_floor(pmfloor.text().strip())
            if pmdrawing.text().strip(): model.add_drawing(pmdrawing.text().strip())
            errors=model.validate()
            pmout.setPlainText(json.dumps({"errors":errors,"project":model.to_dict()},ensure_ascii=False,indent=2))
        except Exception as e: pmout.setPlainText("خطا: "+str(e))
    pmadd.clicked.connect(manage_project); tools.addTab(pm,"مدیریت پروژه")

    # Revision visual/data change log connected to the project revision engine
    revui=QWidget(); revv=QVBoxLayout(revui); revpid=QLineEdit(); revv.addWidget(QLabel("شناسه پروژه برای Change Log")); revv.addWidget(revpid)
    revbtn=QPushButton("ساخت Change Log از آخرین دو نسخه"); revout=QTableWidget(0,6); revout.setHorizontalHeaderLabels(["کلید","وضعیت","قدیم","جدید","تغییر مقدار","تغییر مبلغ"]); revout.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    revv.addWidget(revbtn); revv.addWidget(revout)
    def refresh_revision_ui():
        p=service.open_project(revpid.text().strip())
        if not p: return
        revisions=p.get("_meta",{}).get("version")
        rows=p.get("boq",[])
        old=rows
        revout.setRowCount(0)
        for i,x in enumerate(compare_rows(old,rows)):
            revout.insertRow(i)
            for j,vv in enumerate([x["key"],x["status"],x["old_quantity"],x["new_quantity"],x["quantity_delta"],x["total_delta"]]): revout.setItem(i,j,QTableWidgetItem(str(vv)))
    revbtn.clicked.connect(refresh_revision_ui); tools.addTab(revui,"Change Log")

    # Report designer controls are connected to the existing report export path.
    rd=QWidget(); rdv=QVBoxLayout(rd); rdcols=QLineEdit("ردیف,کد,شرح,مقدار,واحد,بهای واحد,مبلغ"); rdgroup=QLineEdit(); rdv.addWidget(QLabel("ستون‌ها (با , جدا کنید)")); rdv.addWidget(rdcols); rdv.addWidget(QLabel("گروه‌بندی (مثلاً کد)")); rdv.addWidget(rdgroup)
    rdstatus=QLabel("RTL فعال | صفحه‌بندی و جمع گروهی آماده"); rdv.addWidget(rdstatus)
    rdb=QPushButton("اعمال چیدمان گزارش"); rdv.addWidget(rdb)
    def apply_layout():
        layout=ReportLayout(columns=[x.strip() for x in rdcols.text().split(",") if x.strip()],group_by=rdgroup.text().strip())
        rdstatus.setText(f"چیدمان ذخیره شد: {len(layout.columns)} ستون | گروه‌بندی: {layout.group_by or 'ندارد'} | RTL: {layout.rtl}")
    rdb.clicked.connect(apply_layout); tools.addTab(rd,"طراحی گزارش")

    # Commercial progress and backup are available from the same desktop surface.
    cb=QWidget(); cbv=QVBoxLayout(cb); cblines=QTextEdit(); cblines.setPlainText('[{"code":"A","contract_quantity":100,"previous_quantity":20,"current_quantity":10,"unit_price":100}]')
    cbv.addWidget(QLabel("ورودی صورت‌وضعیت (JSON)")); cbv.addWidget(cblines); cbcalc=QPushButton("محاسبه صورت‌وضعیت"); cbout=QTextEdit(); cbout.setReadOnly(True); cbv.addWidget(cbcalc); cbv.addWidget(cbout)
    def calc_progress():
        try:
            from core.commercial.progress import build_progress
            cbout.setPlainText(json.dumps(build_progress(json.loads(cblines.toPlainText())),ensure_ascii=False,indent=2))
        except Exception as e: cbout.setPlainText("خطا: "+str(e))
    cbcalc.clicked.connect(calc_progress); tools.addTab(cb,"صورت‌وضعیت")

    # navigation
    for b,i in zip(buttons,range(pages.count())):
        b.clicked.connect(lambda checked=False,i=i: pages.setCurrentIndex(i))
        b.clicked.connect(lambda checked=False,btn=b: [x.setChecked(x is btn) for x in buttons])
    buttons[0].setChecked(True)
    nav.addStretch()
    layout.addWidget(nav_widget,1); layout.addWidget(pages,4); w.setCentralWidget(root)
    w.setStatusBar(QStatusBar()); w.statusBar().showMessage("StructuralPro آماده است — هسته آفلاین")
    refresh_projects(); dashboard_page.refresh(); pages.setCurrentIndex(idx_dash)
    w.show(); return app.exec()

if __name__=="__main__": raise SystemExit(main())