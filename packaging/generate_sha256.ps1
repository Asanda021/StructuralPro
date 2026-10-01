param(
  [string]$OutputPath = "dist/StructuralPro-SHA256SUMS.txt"
)
$ErrorActionPreference="Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$version=(Get-Content VERSION -Raw).Trim()
$files = @(
  "dist/StructuralPro/StructuralPro.exe",
  "dist/StructuralPro/VERSION"
) | Where-Object { Test-Path $_ }
$installer=Get-ChildItem "dist" -Filter "StructuralPro-$version-Setup.exe" -ErrorAction SilentlyContinue
if ($installer) { $files += $installer.FullName }
if ($files.Count -eq 0) { throw "No release artifacts found" }
$lines = foreach ($file in $files) {
  $hash=(Get-FileHash -Algorithm SHA256 $file).Hash.ToLowerInvariant()
  "$hash  $($file.Replace((Get-Location).Path + '\',''))"
}
New-Item -ItemType Directory -Force (Split-Path -Parent $OutputPath) | Out-Null
$lines | Set-Content -Encoding UTF8 $OutputPath
Write-Host "Wrote $OutputPath"
