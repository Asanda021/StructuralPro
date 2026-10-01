param([string]$Version="")
$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not $Version) { $Version=(Get-Content VERSION -Raw).Trim() }
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean packaging/structuralpro.spec --distpath dist --workpath build
if (-not (Test-Path "dist/StructuralPro/StructuralPro.exe")) { throw "PyInstaller did not create dist/StructuralPro/StructuralPro.exe" }
Write-Host "StructuralPro Windows payload built in dist/StructuralPro (version $Version)"
