"""StructuralPro Windows desktop entry point.
Offline-first shell; core services remain usable without the GUI.
"""
from __future__ import annotations
import sys

def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    except ImportError:
        print("PySide6 is required for the Windows desktop UI. Core modules remain offline-capable.")
        return 2
    app=QApplication(sys.argv)
    w=QMainWindow(); w.setWindowTitle("StructuralPro"); w.resize(1280,800)
    root=QWidget(); layout=QVBoxLayout(root)
    title=QLabel("StructuralPro — متره، برآورد و مدیریت پروژه")
    title.setStyleSheet("font-size:22px;font-weight:700;padding:12px;")
    layout.addWidget(title)
    for text in ("پروژه‌ها","متره از نقشه","فهرست‌بها","صورت‌وضعیت","گزارشات","هوش مصنوعی آفلاین"):
        layout.addWidget(QLabel("• "+text))
    w.setCentralWidget(root); w.show()
    return app.exec()

if __name__=="__main__":
    raise SystemExit(main())
