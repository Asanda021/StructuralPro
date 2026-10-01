"""StructuralPro Windows desktop UI (offline-first dashboard)."""
from __future__ import annotations
import sys
def main()->int:
    try:
        from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QListWidget,QStackedWidget,QStatusBar
        from PySide6.QtCore import Qt
    except ImportError:
        print("PySide6 is required for the Windows desktop UI.")
        return 2
    app=QApplication(sys.argv); app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    w=QMainWindow(); w.setWindowTitle("StructuralPro"); w.resize(1440,900)
    root=QWidget(); layout=QHBoxLayout(root)
    nav=QVBoxLayout(); title=QLabel("StructuralPro"); title.setProperty("role","title"); nav.addWidget(title)
    pages=QStackedWidget()
    sections=[("داشبورد","خلاصه پروژه‌ها، آخرین فعالیت‌ها و وضعیت همگام‌سازی"),
              ("پروژه‌ها","ایجاد، باز کردن، کپی و مدیریت پروژه‌ها"),
              ("متره از نقشه","DWG / DXF / PDF / BIM و متره دستی"),
              ("فهرست‌بها","جستجو، انتخاب و اتصال کد فهرست‌بها"),
              ("برآورد و BOQ","ریز متره، مقادیر، قیمت و جمع"),
              ("صورت‌وضعیت","مقادیر این دوره، تجمعی و کسورات"),
              ("گزارشات","Excel / PDF / Word / CSV"),
              ("هوش مصنوعی آفلاین","کنترل پروژه و دستیار محلی"),
              ("همگام‌سازی","وضعیت آفلاین، صف تغییرات و Sync")]
    for name,desc in sections:
        b=QPushButton(name); b.setMinimumHeight(42); nav.addWidget(b)
        page=QWidget(); v=QVBoxLayout(page); h=QLabel(name); h.setProperty("role","heading"); d=QLabel(desc); d.setWordWrap(True); v.addWidget(h); v.addWidget(d); v.addStretch()
        pages.addWidget(page); b.clicked.connect(lambda checked=False,i=pages.count()-1: pages.setCurrentIndex(i))
    nav.addStretch(); layout.addLayout(nav,1); layout.addWidget(pages,4)
    w.setCentralWidget(root); w.setStatusBar(QStatusBar()); w.statusBar().showMessage("آفلاین آماده است — همگام‌سازی اختیاری")
    w.show(); return app.exec()
if __name__=="__main__": raise SystemExit(main())
