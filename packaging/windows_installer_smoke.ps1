param(
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$ExpectedVersion
)
$ErrorActionPreference = "Stop"

if (-not (Test-Path $Installer)) { throw "Installer not found: $Installer" }
if ($ExpectedVersion -notmatch '^\d+\.\d+\.\d+$') { throw "Invalid expected version: $ExpectedVersion" }

$installDir = Join-Path $env:RUNNER_TEMP "StructuralPro-Installer-Smoke"
if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }

& $Installer /VERYSILENT /NORESTART /SUPPRESSMSGBOXES "/DIR=$installDir"
if ($LASTEXITCODE -ne 0) { throw "Installer exited with code $LASTEXITCODE" }

$exe = Join-Path $installDir "StructuralPro.exe"
$versionFile = Join-Path $installDir "VERSION"
if (-not (Test-Path $exe)) { throw "Installed executable missing: $exe" }
if (-not (Test-Path $versionFile)) { throw "Installed VERSION missing: $versionFile" }

$installedVersion = (Get-Content $versionFile -Raw).Trim()
if ($installedVersion -ne $ExpectedVersion) {
    throw "Installed VERSION '$installedVersion' does not match '$ExpectedVersion'"
}

$env:STRUCTURALPRO_SMOKE = "1"
$env:QT_QPA_PLATFORM = "offscreen"
& $exe
$exitCode = $LASTEXITCODE
Remove-Item Env:STRUCTURALPRO_SMOKE -ErrorAction SilentlyContinue
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue

if ($exitCode -ne 0) { throw "Installed application smoke exited with code $exitCode" }

$uninstaller = Join-Path $installDir "unins000.exe"
if (Test-Path $uninstaller) {
    & $uninstaller /VERYSILENT /NORESTART
    if ($LASTEXITCODE -ne 0) { throw "Uninstaller exited with code $LASTEXITCODE" }
}

Write-Host "Windows installer E2E smoke passed: $ExpectedVersion"
