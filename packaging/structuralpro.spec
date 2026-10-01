from PyInstaller.utils.hooks import collect_submodules

hiddenimports=collect_submodules("core")
a=Analysis(["app/main.py"],pathex=["."],hiddenimports=hiddenimports,datas=[("VERSION",".")],binaries=[],cipher=None)
pyz=PYZ(a.pure,a.zipped_data)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name="StructuralPro",console=False)
