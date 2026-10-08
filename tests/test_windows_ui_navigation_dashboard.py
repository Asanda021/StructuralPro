from pathlib import Path

MAIN = Path("app/main.py").read_text(encoding="utf-8")
THEME = Path("app/theme.py").read_text(encoding="utf-8")
DASHBOARD = Path("app/dashboard.py").read_text(encoding="utf-8")


def test_primary_navigation_is_top_tab_bar():
    assert "QTabBar" in MAIN
    assert "MainNavigationTabs" in MAIN
    assert "nav_tabs.currentChanged.connect(pages.setCurrentIndex)" in MAIN
    assert "layout.addWidget(header)" in MAIN
    assert "layout.addWidget(pages,1)" in MAIN
    assert "layout.addWidget(nav_widget" not in MAIN


def test_dashboard_is_project_first_and_action_oriented():
    assert "گردش‌کار اصلی" in DASHBOARD
    assert "وضعیت سریع" in DASHBOARD
    assert "پروژه‌های اخیر" in DASHBOARD
    assert "self.project_selector" in DASHBOARD
    assert "financial_dashboard" in DASHBOARD
    assert "DashboardAction" in DASHBOARD


def test_theme_has_clear_top_navigation_states():
    assert "#TopShell" in THEME
    assert "#MainNavigationTabs::tab" in THEME
    assert "#MainNavigationTabs::tab:selected" in THEME
    assert "#DashboardSection" in THEME
    assert "#DashboardAction" in THEME
