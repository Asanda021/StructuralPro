from pathlib import Path

def test_commercial_ui_design_tokens_exist():
    css=Path("app/theme.py").read_text(encoding="utf-8")
    for token in ("#PrimaryAction","#SecondaryAction","#KpiCard","#PageTitle","#NavButton"):
        assert token in css

def test_dashboard_and_graphical_takeoff_modules_exist():
    assert Path("app/dashboard.py").exists()
    assert Path("app/graphical_takeoff.py").exists()
