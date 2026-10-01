"""StructuralPro Windows desktop application."""
from __future__ import annotations
import os,sys,tempfile
from pathlib import Path

def main()->int:
    try:
        from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QListWidget,QStackedWidget,QStatusBar,QLineEdit,QComboBox,QFormLayout,QMessageBox,QTextEdit
        from PySide6.QtCore import Qt
        from core.platform.application import StructuralProApp
    except ImportError as exc:
        print("PySide6 and StructuralPro core dependencies are required:",exc); return 2
    app=QApplication(sys.argv); app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    service=StructuralProApp(Path.home()/".structuralpro")
    w=QMainWindow(); w.setWindowTitle("StructuralPro — متره و برآورد"); w.resize(1440,900)
    root=QWidget(); root_layout=QHBoxLayout(root); nav=QVBoxLayout(); pages=QStackedWidget()
    sections=[("داشبورد","داشبورد پروژه و وضعیت آفلاین"),
              ("پروژه‌ها","ساخت و بازکردن پروژه"),
              ("متره سریع","ورود سریع متره با انتخاب‌های آماده"),
              ("فهرست‌بها","جستجو و اتصال کدهای قیمت"),
              ("برآورد و BOQ","جمع مقادیر و هزینه"),
              ("صورت‌وضعیت","مقادیر جاری و تجمعی"),
              ("گزارشات","خروجی Excel / PDF / Word / CSV"),
              ("هوش مصنوعی آفلاین","کنترل نقص اطلاعات پروژه"),
              ("همگام‌سازی","همگام‌سازی اختیاری")]
    for name,desc in sections:
        b=QPushButton(name); b.setMinimumHeight(44); nav.addWidget(b)
        page=QWidget(); v=QVBoxLayout(page); v.addWidget(QLabel(name)); v.addWidget(QLabel(desc))
        if name=="پروژه‌ها":
            form=QFormLayout(); pid=QLineEdit(); pname=QLineEdit(); create=QPushButton("ایجاد پروژه"); out=QLabel()
            form.addRow("شناسه:",pid); form.addRow("نام پروژه:",pname); v.addLayout(form); v.addWidget(create); v.addWidget(out)
            create.clicked.connect(lambda: (service.create_project(pid.text().strip() or "project",pname.text().strip() or "پروژه جدید"),out.setText("پروژه ذخیره شد؛ قابل استفاده آفلاین است.")))
        elif name=="متره سریع":
            form=QFormLayout(); pid=QLineEdit(); item=QComboBox(); item.addItems(["slab","wall","column","beam","footing_concrete"])
            length=QLineEdit(); width=QLineEdit(); height=QLineEdit(); calc=QPushButton("محاسبه و ثبت"); out=QTextEdit(); out.setReadOnly(True)
            for x,label in ((pid,"شناسه پروژه"),(length,"طول"),(width,"عرض"),(height,"ارتفاع")): form.addRow(label,x)
            form.addRow("آیتم",item); v.addLayout(form); v.addWidget(calc); v.addWidget(out)
            def do_calc():
                try:
                    params={"length":float(length.text() or 0),"width":float(width.text() or 0),"height":float(height.text() or 0)}
                    row=service.add_takeoff(pid.text().strip(),"building",item.currentText(),**params)
                    out.setPlainText(f"ثبت شد\nمقدار: {row['quantities'][0]['amount']} {row['quantities'][0]['unit']}")
                except Exception as e: out.setPlainText("خطا: "+str(e))
            calc.clicked.connect(do_calc)
        elif name=="هوش مصنوعی آفلاین":
            pid=QLineEdit(); check=QPushButton("کنترل پروژه"); out=QTextEdit(); out.setReadOnly(True)
            v.addWidget(pid); v.addWidget(check); v.addWidget(out)
            check.clicked.connect(lambda: out.setPlainText("\n".join(f"{x.get('severity','')}: {x.get('message','')}" for x in service.validate(pid.text().strip())) or "ایراد ضروری پیدا نشد."))
        else:
            v.addStretch()
        pages.addWidget(page); b.clicked.connect(lambda checked=False,i=pages.count()-1: pages.setCurrentIndex(i))
    nav.addWidget(QLabel("Ctrl+N  پروژه جدید   |   Ctrl+S ذخیره   |   F5 بازبینی")); nav.addStretch()
    root_layout.addLayout(nav,1); root_layout.addWidget(pages,4); w.setCentralWidget(root)
    w.setStatusBar(QStatusBar()); w.statusBar().showMessage("آفلاین آماده است — همگام‌سازی اختیاری")
    w.show(); return app.exec()

if __name__=="__main__": raise SystemExit(main())
