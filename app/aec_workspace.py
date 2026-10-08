"""Functional AEC takeoff workspaces: concrete/steel/architecture and real roof quantity rules."""
from __future__ import annotations
from PySide6.QtWidgets import (
    QComboBox,QDoubleSpinBox,QFormLayout,QGroupBox,QLabel,QLineEdit,QMessageBox,
    QPushButton,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget,QHeaderView
)

ITEMS={
"architecture":[
("wall","دیوار",("length","height","openings")),("slab","کف / سطح",("length","width")),
("plaster","گچ‌کاری",("length","height","openings","count")),("tile","کاشی / سرامیک",("length","height","openings","waste")),
("roof_insulation","عایق‌کاری بام",("length","width","layers")),("door","درب",("count",)),("window","پنجره",("count",)),
("facade","نما",("length","height","openings")),("ceiling","سقف کاذب",("length","width","count"))],
"structural_concrete":[
("footing_concrete","پی / فونداسیون بتنی",("length","width","thickness","count")),
("tie_beam","شناژ / کلاف بتنی",("length","width","depth","count")),
("column","ستون بتنی",("width","depth","height","count")),("beam","تیر بتنی",("length","width","depth","count")),
("shear_wall","دیوار برشی بتنی",("length","thickness","height","count")),
("stair_concrete","پله بتنی",("length","width","thickness","count")),
("formwork","قالب‌بندی",("perimeter","height","count")),("rebar","آرماتور",("length","unit_weight","count")),
("solid_slab_roof","سقف دال بتنی توپر / دال تخت — حجم بتن",("length","width","thickness","count")),
("joist_block_roof","سقف تیرچه‌بلوک — حجم بتن",("length","width","topping_thickness","joist_spacing","joist_width","joist_depth","count")),
("joist_foam_roof","سقف تیرچه‌فوم — حجم بتن",("length","width","topping_thickness","joist_spacing","joist_width","joist_depth","count")),
("hollow_core_roof","سقف دال مجوف — حجم بتن",("length","width","thickness","void_diameter","void_count","count")),
("waffle_roof","سقف وافل — حجم بتن",("length","width","top_thickness","spacing_x","spacing_y","rib_width","rib_depth","count")),
("uboot_roof","سقف یوبوت — حجم بتن خالص",("length","width","thickness","void_length","void_width","void_height","void_count","count")),
("cobiax_roof","سقف کوبیاکس — حجم بتن خالص",("length","width","thickness","void_length","void_width","void_height","void_count","count"))],
"structural_steel":[
("steel","عضو فولادی / تیر / ستون",("length","unit_weight","count")),
("steel_roof_deck_area","سقف عرشه فولادی — مساحت عرشه",("length","width","count")),
("steel_roof_deck_weight","سقف عرشه فولادی — وزن ورق",("length","width","sheet_weight","count")),
("steel_roof_composite_concrete","سقف کامپوزیت — حجم بتن",("length","width","thickness","count")),
("steel_roof_composite_deck","سقف کامپوزیت — وزن ورق",("length","width","sheet_weight","count")),
("kromit_roof","سقف تیرچه کرومیت — وزن تیرچه",("joist_length","joist_unit_weight","joist_count","count")),
("steel_truss_roof","سقف خرپایی فولادی — وزن فولاد",("steel_length","unit_weight","count")),
("steel_sandwich_roof","سقف ساندویچ‌پنل روی سازه فولادی — مساحت پنل",("length","width","count"))],
"masonry":[("wall","دیوار بنایی",("length","height","openings"))],
"mechanical":[("pipe","لوله",("length","count")),("duct","کانال",("length","count")),("duct_area","سطح کانال",("width","height","length")),("insulation","عایق لوله",("diameter","length")),("equipment","تجهیزات",("count",)),("valve","شیر / اتصال",("count",))],
"electrical":[("cable","کابل / سیم",("length","count")),("conduit","لوله برق",("length","count")),("panel","تابلو",("count",)),("light","روشنایی",("count",)),("socket","پریز",("count",)),("earthing","ارت",("length",)),("cable_tray","سینی کابل",("length","count"))],
"civil":[("excavation","خاکبرداری",("length","width","depth")),("backfill","خاکریزی",("excavation","deductions")),("paving","بتن محوطه",("length","width","thickness")),("asphalt","آسفالت",("length","width","thickness")),("curb","جدول",("length","count")),("drainage","زهکشی",("length",)),("fence_wall","دیوارکشی",("length","height"))],
"renovation":[("demolition","تخریب",("length","width","height","count")),("facade","نما / مرمت نما",("length","height","openings")),("screed","کف‌سازی",("length","width","thickness","count")),("ceiling","سقف کاذب",("length","width","count"))],
}

FIELDS={
"length":"طول","width":"عرض","height":"ارتفاع","depth":"عمق","thickness":"ضخامت","perimeter":"محیط",
"count":"تعداد","unit_weight":"وزن واحد (kg/m)","openings":"کسر بازشو (m²)","waste":"ضریب پرت",
"layers":"تعداد لایه","diameter":"قطر","excavation":"حجم خاکبرداری","deductions":"کسرها",
"topping_thickness":"ضخامت بتن رویه","joist_spacing":"فاصله آکس تیرچه","joist_width":"عرض تیرچه",
"joist_depth":"عمق مؤثر تیرچه","void_diameter":"قطر فضای خالی","void_count":"تعداد فضای خالی",
"top_thickness":"ضخامت رویه","spacing_x":"فاصله آکس در جهت X","spacing_y":"فاصله آکس در جهت Y",
"rib_width":"عرض تیرچه وافل","rib_depth":"عمق مؤثر تیرچه وافل","void_length":"طول فضای خالی",
"void_width":"عرض فضای خالی","void_height":"ارتفاع فضای خالی","sheet_weight":"وزن ورق (kg/m²)",
"joist_length":"طول تیرچه","joist_unit_weight":"وزن واحد تیرچه (kg/m)","joist_count":"تعداد تیرچه",
"steel_length":"طول کل فولاد",
}

ITEM_DOMAINS={"footing_concrete":"advanced","steel":"advanced","steel_roof_deck_area":"advanced",
"steel_roof_deck_weight":"advanced","steel_roof_composite_concrete":"building",
"steel_roof_composite_deck":"advanced","kromit_roof":"advanced","steel_truss_roof":"advanced"}

def build_aec_workspace(service,catalog,*,title,description,domain,key,status_callback=None):
    root=QWidget(); root.setObjectName("AECWorkspace"); outer=QVBoxLayout(root); outer.setSpacing(14)
    h=QLabel(title); h.setObjectName("PageTitle"); d=QLabel(description); d.setObjectName("PageDescription"); d.setWordWrap(True)
    outer.addWidget(h); outer.addWidget(d)
    box=QGroupBox("ریزمتره و محاسبه واقعی"); grid=QFormLayout(box)
    project=QLineEdit(); project.setPlaceholderText("شناسه پروژه موجود")
    item=QComboBox(); price=QLineEdit(); price.setPlaceholderText("اختیاری؛ کد فهرست‌بهای واردشده توسط کاربر")
    specs={c:f for c,_,f in ITEMS[key]}; labels={c:l for c,l,_ in ITEMS[key]}
    for c,l,_ in ITEMS[key]: item.addItem(l,c)
    grid.addRow("پروژه",project); grid.addRow("آیتم / نوع سقف",item); grid.addRow("کد فهرست‌بها (اختیاری)",price)
    fields={}
    for name,label in FIELDS.items():
        w=QDoubleSpinBox(); w.setDecimals(4); w.setRange(0,1000000000); w.setSingleStep(.1)
        w.setValue(1 if name in {"count","layers","waste"} else 0); fields[name]=w; grid.addRow(label,w)
    calc=QPushButton("محاسبه و ثبت واقعی"); calc.setObjectName("PrimaryAction"); grid.addRow(calc); outer.addWidget(box)
    note=QLabel("هیچ ضریب یا مقدار ثابت برای سقف‌های غیر یکنواخت اعمال نمی‌شود؛ ابعاد واقعی نقشه/مشخصات فنی باید وارد شود.")
    note.setObjectName("DashboardNotice"); note.setWordWrap(True); outer.addWidget(note)
    result=QLabel("نتیجه پس از محاسبه در پروژه و BOQ ثبت می‌شود."); result.setWordWrap(True); outer.addWidget(result)
    table=QTableWidget(0,8); table.setHorizontalHeaderLabels(["شناسه","آیتم","مقدار","واحد","فرمول","کد فهرست‌بها","منبع","هشدار"]); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); outer.addWidget(table,1)
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
                vals=[q.get("id",""),q.get("title",""),q.get("amount",""),q.get("unit",""),q.get("formula",""),q.get("price_code","") or "—",q.get("source","manual"),q.get("warning","") or "—"]
                for j,v in enumerate(vals): table.setItem(i,j,QTableWidgetItem(str(v)))
        except Exception: pass
    def calculate():
        pid=project.text().strip()
        if not pid: QMessageBox.warning(root,"متره","ابتدا شناسه پروژه را وارد کنید."); return
        code=item.currentData(); params={n:float(w.value()) for n,w in fields.items() if w.isEnabled()}; params["member_code"]=code
        pc=price.text().strip()
        if pc:
            resolved=catalog.resolve(pc)
            if resolved.get("status")!="ok":
                QMessageBox.warning(root,"فهرست‌بها","کد در فهرست‌بهای واردشده پیدا نشد."); return
            params["price_code"]=pc; params["unit_price"]=resolved["unit_price"]
        else: params["price_code"]=None
        try:
            p=service.open_project(pid); source_id=f"manual:{key}:{code}:{len(p.get('takeoffs',[]))+1}"
            effective_domain=ITEM_DOMAINS.get(code,domain)
            row=service.add_takeoff(pid,effective_domain,code,source_id=source_id,description=labels[code],**params)
            q=row["quantities"][0]
            result.setText(f"🟢 ثبت شد | {labels[code]} | {q['amount']:,.4f} {q['unit']} | فرمول: {q['formula']}")
            refresh()
            if status_callback: status_callback(f"متره {title} ثبت شد")
        except Exception as exc: QMessageBox.critical(root,"خطای متره",str(exc))
    item.currentIndexChanged.connect(update_fields); calc.clicked.connect(calculate); project.editingFinished.connect(refresh); update_fields()
    return root
