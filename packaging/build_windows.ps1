param([string]$Version="0.1.0")
$ErrorActionPreference="Stop"
py -3.12 -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onedir --windowed --name StructuralPro app/main.py
Write-Host "StructuralPro Windows payload built in dist/StructuralPro"
