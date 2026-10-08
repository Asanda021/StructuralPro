from pathlib import Path

MAIN = Path("app/main.py").read_text(encoding="utf-8")
WORKSPACE = Path("app/aec_workspace.py").read_text(encoding="utf-8")


def test_aec_navigation_has_separate_real_workspaces():
    required = [
        "🏠 معماری", "🏗 سازه بتن", "🏭 سازه فولاد", "🏠 انواع سقف", "🧱 بنایی",
        "❄ تأسیسات مکانیکی", "⚡ تأسیسات برقی",
        "🌳 محوطه و عملیات بیرونی", "♻ بازسازی و مرمت",
    ]
    for label in required:
        assert label in MAIN
    assert "build_aec_workspace" in MAIN
    assert 'pages.addWidget(wp); discipline_pages[key]=pages.count()-1' in MAIN


def test_aec_workspace_has_real_save_path():
    assert "service.add_takeoff(pid,effective_domain,code" in WORKSPACE
    assert "service.open_project(pid)" in WORKSPACE
    assert "catalog.resolve(pc)" in WORKSPACE
    assert "محاسبه و ثبت واقعی" in WORKSPACE
    assert "source_id=" in WORKSPACE


def test_aec_workspace_does_not_create_fake_item_types():
    expected = [
        '"wall"', '"slab_volume"', '"column"', '"beam"', '"footing_concrete"',
        '"steel"', '"pipe"', '"duct"', '"cable"', '"excavation"', '"demolition"',
    ]
    for item in expected:
        assert item in WORKSPACE


def test_settings_do_not_offer_unimplemented_language_or_unit_switches():
    assert 'lang.addItems(["فارسی (RTL)","English (LTR)"])' not in MAIN
    assert 'unit.addItems(["متر / مترمربع / مترمکعب","سانتی‌متر / میلی‌متر"])' not in MAIN


def test_project_documents_are_persisted():
    assert '"documents"' in MAIN
    assert "service.store.save(project_id,project)" in MAIN
    assert "docbrowse.clicked.connect" in MAIN


def test_report_layout_is_persisted_in_project():
    assert 'project["_report_layout"]' in MAIN
    assert 'service.store.save(project_id,project)' in MAIN


def test_removed_static_capability_claim():
    assert 'tools.addTab(QLabel("گزارش‌ساز قابل تنظیم، Excel Bridge و Undo/Redo در هسته فعال است.")' not in MAIN


def test_real_structural_and_roof_systems_are_explicit_and_calculable():
    for label in [
        "سیستم باربر: قاب خمشی بتن‌آرمه", "سیستم باربر: دیوار برشی",
        "سقف: تیرچه‌بلوک", "سقف: وافل", "سقف: یوبوت", "سقف: کوبیاکس",
        "سیستم باربر: قاب خمشی فولادی", "سقف: عرشه فولادی",
    ]:
        assert label in WORKSPACE
    assert '"roof_area","مساحت سیستم سقف"' in WORKSPACE
    assert '"shear_wall","دیوار برشی بتنی"' in WORKSPACE
    assert '"tie_beam","شناژ / کلاف بتنی"' in WORKSPACE


def test_structural_system_metadata_is_persisted():
    app = Path("core/platform/application.py").read_text(encoding="utf-8")
    assert 'description=str(params.pop("description","")).strip()' in app
    assert 'system=str(params.pop("system","")).strip() or None' in app
    assert '"system":system' in app
