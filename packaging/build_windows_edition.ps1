param([Parameter(Mandatory=$true)][string]$Version,[Parameter(Mandatory=$true)][ValidateSet("light","standard","pro","enterprise")][string]$Edition)
$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$canonicalVersion=(Get-Content VERSION -Raw).Trim()
if ($Version -ne $canonicalVersion) { throw "Requested version '$Version' does not match VERSION '$canonicalVersion'" }
& "$PSScriptRoot/build_windows.ps1" -Version $Version
if ($LASTEXITCODE -ne 0) { throw "Base Windows payload build failed" }
$payload="dist/StructuralPro"
if (-not (Test-Path "$payload/StructuralPro.exe")) { throw "Missing Windows executable" }
Set-Content "$payload/EDITION" -Value $Edition -Encoding ascii
Set-Content "$payload/EDITION_VERSION" -Value "$Edition@$Version" -Encoding ascii
$template=Get-Content "$PSScriptRoot/installer-edition.iss" -Raw
$generated=$template.Replace("__VERSION__",$Version).Replace("__EDITION__",$Edition)
$generatedPath="build/installer-$Edition-$Version.iss"
New-Item -ItemType Directory -Force build | Out-Null
Set-Content $generatedPath -Value $generated -Encoding utf8
$iscc=Get-Command "C:Program Files (x86)Inno Setup 6ISCC.exe" -ErrorAction SilentlyContinue
if (-not $iscc) { throw "Inno Setup compiler not found" }
& $iscc.Source $generatedPath
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed: $LASTEXITCODE" }
$installer="dist/StructuralPro-$Edition-$Version-Setup.exe"
if (-not (Test-Path $installer)) { throw "Edition installer missing: $installer" }
if ((Get-Item $installer).Length -lt 1024) { throw "Edition installer is implausibly small" }
if ((Get-Content "$payload/EDITION" -Raw).Trim() -ne $Edition) { throw "Edition marker mismatch" }
Write-Host "Built StructuralPro $Edition edition $Version"
