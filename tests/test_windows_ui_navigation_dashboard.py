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


def test_navigation_uses_clear_professional_symbols():
    assert "⌂ داشبورد" in MAIN
    assert "📁 پروژه‌ها" in MAIN
    assert "📐 متره سریع" in MAIN
    assert "💰 فهرست‌بها" in MAIN
    assert "🤖 هوش مصنوعی آفلاین" in MAIN


def test_pricebook_is_real_file_import_workflow():
    assert "PricebookImportService" in MAIN
    assert "📥 ورود Excel / CSV" in MAIN
    assert "Excel (*.xlsx *.xlsm)" in MAIN
    assert "catalog.resolve" in MAIN
    assert "catalog.export_csv" in MAIN


def test_contextual_command_ribbon_reuses_existing_workflows():
    assert "CommandRibbon" in MAIN
    assert "RibbonPrimary" in MAIN
    assert "refresh_command_ribbon" in MAIN
    assert 'add_command("📥 ورود Excel/CSV", load_prices, True)' in MAIN
    assert 'add_command("➕ ایجاد پروژه", create.click, True)' in MAIN
    assert 'add_command("📄 انتخاب/بررسی نقشه", browse.click, True)' in MAIN
    assert 'add_command("🔄 بازسازی برآورد", show_boq, True)' in MAIN
    assert 'add_command("🧮 محاسبه دوره", statement_shortcut, True)' in MAIN


def test_user_pricebook_is_persisted_locally():
    assert 'pricebook_store=Path.home()/".structuralpro"/"pricebook_user.csv"' in MAIN
    assert 'catalog.import_csv(pricebook_store.read_text' in MAIN
    assert 'pricebook_store.write_text(catalog.export_csv' in MAIN


def test_quick_takeoff_preserves_selected_discipline():
    assert 'service.add_takeoff(qpid.text().strip(),discipline.currentData() or "building"' in MAIN
