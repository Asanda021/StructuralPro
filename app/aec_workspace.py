"""AEC discipline workspaces for the StructuralPro Windows desktop UI."""
from __future__ import annotations
from PySide6.QtWidgets import QComboBox,QDoubleSpinBox,QFormLayout,QGroupBox,QLabel,QLineEdit,QMessageBox,QPushButton,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget,QHeaderView

ITEMS={
"architecture":[("wall","دیوار",("length","height","openings")),("slab","کف / سقف",("length","width")),("plaster","گچ‌کاری",("length","height","openings","count")),("tile","کاشی / سرامیک",("length","height","openings","waste")),("roof_insulation","عایق‌کاری",("length","width","layers")),("door","درب",("count",)),("window","پنجره",("count",)),("facade","نما",("length","height","openings")),("ceiling","سقف کاذب",("length","width","count"))],
"structural_concrete":[("slab_volume","بتن سقف",("length","width","thickness")),("column","بتن ستون",("width","depth","height","count")),("beam","بتن تیر",("length","width","depth","count")),("footing_concrete","بتن فونداسیون",("length","width","thickness","count")),("formwork","قالب‌بندی",("perimeter","height","count")),("rebar","آرماتور",("length","unit_weight","count"))],
"structural_steel":[("steel","اسکلت / مقاطع فولادی",("length","unit_weight","count"))],
"masonry":[("wall","دیوار بنایی",("length","height","openings"))],
"mechanical":[("pipe","لوله",("length","count")),("duct","کانال",("length","count")),("duct_area","سطح کانال",("width","height","length")),("insulation","عایق لوله",("diameter","length")),("equipment","تجهیزات",("count",)),("valve","شیر / اتصال",("count",))],
"electrical":[("cable","کابل / سیم",("length","count")),("conduit","لوله برق",("length","count")),("panel","تابلو",("count",)),("light","روشنایی",("count",)),("socket","پریز",("count",)),("earthing","ارت",("length",)),("cable_tray","سینی کابل",("length",))],
"civil":[("excavation","خاکبرداری",("length","width","depth")),("backfill","خاکریزی",("excavation","deductions")),("paving","بتن محوطه",("length","width","thickness")),("asphalt","آسفالت",("length","width","thickness")),("curb","جدول",("length","count")),("drainage","زهکشی",("length",)),("fence_wall","دیوارکشی",("length","height"))],
"renovation":[("demolition","تخریب",("length","width","height","count")),("facade","نما / مرمت نما",("length","height","openings")),("screed","کف‌سازی",("length","width","thickness","count")),("ceiling","سقف کاذب",("length","width","count"))],
}
ITEM_DOMAINS={"footing_concrete":"advanced","steel":"advanced"}
FIELDS={"length":"طول","width":"عرض","height":"ارتفاع","depth":"عمق","thickness":"ضخامت","perimeter":"محیط","count":"تعداد","unit_weight":"وزن واحد (kg/m)","openings":"کسر بازشو (m²)","waste":"ضریب پرت","layers":"تعداد لایه","diameter":"قطر","excavation":"حجم خاکبرداری","deductions":"کسرها"}

def build_aec_workspace(service,catalog,*,title,description,domain,key,status_callback=None):
    root=QWidget(); root.setObjectName("AECWorkspace"); outer=QVBoxLayout(root); outer.setSpacing(14)
    h=QLabel(title); h.setObjectName("PageTitle"); d=QLabel(description); d.setObjectName("PageDescription"); d.setWordWrap(True); outer.addWidget(h); outer.addWidget(d)
    box=QGroupBox("ورود و محاسبه متره"); grid=QFormLayout(box); project=QLineEdit(); project.setPlaceholderText("شناسه پروژه موجود"); item=QComboBox(); price=QLineEdit(); price.setPlaceholderText("اختیاری؛ کد فهرست‌بها")
    specs={c:f for c,_,f in ITEMS[key]}; labels={c:l for c,l,_ in ITEMS[key]}
    for c,l,_ in ITEMS[key]: item.addItem(l,c)
    grid.addRow("پروژه",project); grid.addRow("آیتم",item); grid.addRow("کد فهرست‌بها",price)
    fields={}
    for name,label in FIELDS.items():
        w=QDoubleSpinBox(); w.setDecimals(4); w.setRange(0,1000000000); w.setSingleStep(.1); w.setValue(1 if name in {"count","layers","waste"} else 0); fields[name]=w; grid.addRow(label,w)
    calc=QPushButton("محاسبه و ثبت واقعی"); calc.setObjectName("PrimaryAction"); grid.addRow(calc); outer.addWidget(box)
    result=QLabel("برای ثبت متره، پروژه و پارامترهای موردنیاز آیتم را وارد کنید."); result.setObjectName("DashboardNotice"); result.setWordWrap(True); outer.addWidget(result)
    table=QTableWidget(0,7); table.setHorizontalHeaderLabels(["شناسه","آیتم","مقدار","واحد","فرمول","کد فهرست‌بها","منبع"]); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); table.setAlternatingRowColors(True); outer.addWidget(table,1)
    def update_fields():
        active=set(specs[item.currentData()])
        for n,w in fields.items():
            w.setEnabled(n in active)
            if n not in active: w.setValue(0)
            elif n in {"count","layers","waste"} and w.value()==0: w.setValue(1)
    def refresh():
        pid=project.text().strip()
        if not pid:return
        try:
            p=service.open_project(pid)
            if not p:return
            rows=[q for t in p.get("takeoffs",[]) for q in t.get("quantities",[]) if q.get("code")==item.currentData()]
            table.setRowCount(0)
            for i,q in enumerate(rows[-100:]):
                table.insertRow(i)
                for j,v in enumerate([q.get("id",""),q.get("title",""),q.get("amount",""),q.get("unit",""),q.get("formula",""),q.get("price_code","") or "—",q.get("source","manual")]): table.setItem(i,j,QTableWidgetItem(str(v)))
        except Exception: pass
    def calculate():
        pid=project.text().strip()
        if not pid: QMessageBox.warning(root,"متره","ابتدا شناسه یک پروژه موجود را وارد کنید."); return
        code=item.currentData(); params={n:float(w.value()) for n,w in fields.items() if w.isEnabled()}; params["member_code"]=code
        pc=price.text().strip()
        if pc:
            resolved=catalog.resolve(pc)
            if resolved.get("status")!="ok": QMessageBox.warning(root,"فهرست‌بها","کد فهرست‌بها در کتابخانه فعلی پیدا نشد."); return
            params["price_code"]=pc; params["unit_price"]=resolved["unit_price"]
        else: params["price_code"]=None
        try:
            p=service.open_project(pid); source_id=f"manual:{key}:{code}:{len(p.get('takeoffs',[]))+1}"
            effective_domain=ITEM_DOMAINS.get(code,domain)
            row=service.add_takeoff(pid,effective_domain,code,source_id=source_id,**params); q=row["quantities"][0]
            result.setText(f"🟢 ثبت شد | {labels[code]} | {q['amount']:,.4f} {q['unit']} | فرمول: {q['formula']}"); refresh()
            if status_callback: status_callback(f"متره {title} ثبت شد")
        except Exception as exc: QMessageBox.critical(root,"خطای متره",str(exc))
    item.currentIndexChanged.connect(update_fields); calc.clicked.connect(calculate); project.editingFinished.connect(refresh); update_fields()
    return root
