"""StructuralPro professional RTL desktop theme."""
APP_STYLESHEET = r"""
* { font-family: "Vazirmatn","Segoe UI",Tahoma,sans-serif; font-size: 10.5pt; }
QMainWindow, QWidget { background: #f4f7fb; color: #172033; }
#NavigationPanel { background: #10233f; border-left: 1px solid #d6deea; }
#BrandTitle { color: white; font-size: 22pt; font-weight: 800; padding: 8px 12px 4px; }
#NavigationPanel QLabel { color: #dbe7f7; }
#NavButton { color: #dbe7f7; background: transparent; border: 0; border-radius: 8px; padding: 10px 14px; text-align: right; }
#NavButton:hover { background: #1b385f; }
#NavButton:checked { background: #245a91; color: white; font-weight: 700; }
#ContentPage { background: #f7f9fc; }
#PageTitle { color: #12233f; font-size: 20pt; font-weight: 800; }
#PageDescription { color: #62708a; font-size: 10.5pt; }
#SectionTitle { color: #17345b; font-size: 13pt; font-weight: 700; padding-top: 6px; }
#DashboardCard, QGroupBox { background: white; border: 1px solid #dce4ef; border-radius: 10px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit { background: white; border: 1px solid #cbd6e4; border-radius: 7px; padding: 7px; selection-background-color: #2d6da3; }
QPushButton { background: #e8eef6; border: 1px solid #cbd6e4; border-radius: 7px; padding: 8px 13px; min-height: 32px; }
QPushButton:hover { background: #dce8f5; }
#PrimaryAction { background: #1769aa; color: white; border: 0; font-weight: 700; }
#PrimaryAction:hover { background: #0f5b97; }
#SecondaryAction { background: white; border: 1px solid #8aa8c5; color: #204e76; font-weight: 600; }
QTableWidget { background: white; border: 1px solid #d6dfeb; border-radius: 8px; gridline-color: #e5ebf3; alternate-background-color: #f7fafd; }
QHeaderView::section { background: #e9eff7; color: #253957; padding: 8px; border: 0; border-bottom: 1px solid #d4deea; font-weight: 700; }
QStatusBar { background: #10233f; color: #e7f0fb; }
QToolTip { background: #172b47; color: white; border: 0; padding: 6px; }
QTabBar::tab { background: #e8eef6; padding: 9px 16px; border: 1px solid #d1dbe8; }
QTabBar::tab:selected { background: white; font-weight: 700; }
"""
