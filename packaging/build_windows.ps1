param([string]$Version="")
$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$canonicalVersion=(Get-Content VERSION -Raw).Trim()
if (-not $Version) { $Version=$canonicalVersion }
if ($Version -ne $canonicalVersion) { throw "Requested build version '$Version' does not match VERSION '$canonicalVersion'" }
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "Invalid VERSION format: $Version" }

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean packaging/structuralpro.spec --distpath dist/StructuralPro --workpath build

$exe="dist/StructuralPro/StructuralPro.exe"
$embedded="dist/StructuralPro/VERSION"
if (-not (Test-Path $exe)) { throw "PyInstaller did not create $exe" }
if (-not (Test-Path $embedded)) { throw "Packaged VERSION is missing" }
$packagedVersion=(Get-Content $embedded -Raw).Trim()
if ($packagedVersion -ne $canonicalVersion) { throw "Packaged VERSION '$packagedVersion' does not match canonical VERSION '$canonicalVersion'" }

Write-Host "StructuralPro Windows payload built and version-validated: $canonicalVersion"
