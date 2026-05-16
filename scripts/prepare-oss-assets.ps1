# One-time helper: copy generated logos into docs/assets and remove local build junk.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Assets = Join-Path $Root "docs\assets"
& (Join-Path $PSScriptRoot "copy-logos.ps1")

$removeFiles = @(
    "e501.json",
    "README.public.md",
    "package.json",
    "backend\wheel.json"
)
foreach ($rel in $removeFiles) {
    $path = Join-Path $Root $rel
    if (Test-Path $path) {
        Remove-Item -Force $path
        Write-Host "Removed $rel"
    }
}

Get-ChildItem -Recurse (Join-Path $Root "backend\sandesh") -Filter "*.c" -ErrorAction SilentlyContinue |
    Remove-Item -Force

foreach ($dir in @("backend\build", "backend\dist", "backend\sandesh_sdk.egg-info")) {
    $path = Join-Path $Root $dir
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
        Write-Host "Removed $dir"
    }
}

Write-Host "Done."
