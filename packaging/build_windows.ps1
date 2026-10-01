$ErrorActionPreference = "Stop"
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 -m PyInstaller --noconfirm --clean packaging/structuralpro.spec
Write-Host "StructuralPro Windows build completed: dist\\StructuralPro"
