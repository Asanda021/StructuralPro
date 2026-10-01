"""StructuralPro visual system derived from the approved Canva UI concept."""
from __future__ import annotations

APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #F5F7FA;
    color: #172033;
    font-family: "Segoe UI", "Tahoma";
    font-size: 10.5pt;
}
QLabel#BrandTitle {
    color: #FFFFFF;
    font-size: 22px;
    font-weight: 800;
    padding: 10px 12px;
}
QLabel#PageTitle {
    color: #111827;
    font-size: 22px;
    font-weight: 800;
    padding-top: 4px;
}
QLabel#PageDescription {
    color: #64748B;
    font-size: 10.5pt;
    padding-bottom: 8px;
}
QLabel#StatusPill {
    color: #CFE7D5;
    background: #1F2937;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 10px;
}
QWidget#NavigationPanel {
    background: #111827;
    border: none;
}
QPushButton {
    background: #FFFFFF;
    border: 1px solid #D8DEE8;
    border-radius: 7px;
    padding: 8px 12px;
    min-height: 34px;
}
QPushButton:hover {
    background: #EEF5FF;
    border-color: #7AA7E8;
}
QPushButton:pressed {
    background: #DDEBFF;
}
QPushButton#NavButton {
    color: #D8DEE8;
    background: transparent;
    border: none;
    border-radius: 7px;
    text-align: right;
    padding: 10px 14px;
    min-height: 38px;
}
QPushButton#NavButton:hover {
    background: #1F2937;
    color: #FFFFFF;
}
QPushButton#NavButton:checked {
    background: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
    padding-right: 18px;
}
QPushButton#NavButton:checked:hover {
    background: #1D4ED8;
}
QTabWidget::pane {
    border: 1px solid #D8DEE8;
    background: #FFFFFF;
    border-radius: 8px;
    padding: 6px;
}
QTabBar::tab {
    background: #EEF2F7;
    color: #334155;
    padding: 8px 14px;
    margin-left: 3px;
    border-radius: 6px;
}
QTabBar::tab:selected {
    background: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
}
QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background: #FFFFFF;
    border: 1px solid #D5DBE5;
    border-radius: 7px;
    padding: 7px 9px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #4D8FEA;
}
QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #F8FAFC;
    gridline-color: #E2E8F0;
    border: 1px solid #D8DEE8;
    border-radius: 7px;
}
QHeaderView::section {
    background: #EAF0F7;
    color: #243047;
    font-weight: 700;
    padding: 8px;
    border: none;
}
QGroupBox {
    background: #FFFFFF;
    border: 1px solid #D8DEE8;
    border-radius: 9px;
    margin-top: 12px;
    padding: 12px;
    font-weight: 700;
}
QStatusBar {
    background: #111827;
    color: #D8DEE8;
}
"""
