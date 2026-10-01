# PyInstaller specification for the StructuralPro desktop client.
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("core")

block_cipher = None


a = Analysis(["app/main.py"], pathex=["."], hiddenimports=hiddenimports, datas=[], binaries=[], cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="StructuralPro", console=False)
