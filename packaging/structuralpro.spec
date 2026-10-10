import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_all

ROOT = Path.cwd()

if not (ROOT / "app" / "main.py").exists():
    raise FileNotFoundError(f"Application entrypoint not found under {ROOT}")

hiddenimports = collect_submodules("core")
datas = [(str(ROOT / "VERSION"), ".")]
binaries = []
if os.environ.get("STRUCTURALPRO_BUNDLE_IFC") == "1":
    import ifcopenshell  # Missing dependency must stop an explicitly requested BIM build.
    ifc_datas, ifc_binaries, ifc_hiddenimports = collect_all("ifcopenshell")
    datas += ifc_datas
    datas += [(str(ROOT / "third_party" / name), "licenses/ifcopenshell")
              for name in ("IFCOPENSHELL_COPYING.txt", "IFCOPENSHELL_COPYING_LESSER.txt", "IFCOPENSHELL_NOTICE.txt")]
    binaries += ifc_binaries
    hiddenimports += ifc_hiddenimports
a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    hiddenimports=hiddenimports,
    datas=datas,
    binaries=binaries,
    cipher=None,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="StructuralPro", console=False)