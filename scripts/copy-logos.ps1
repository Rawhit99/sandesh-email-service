$Assets = Join-Path (Split-Path -Parent $PSScriptRoot) "docs\assets"
$Src = Join-Path $env:USERPROFILE ".cursor\projects\c-Users-RohitThakur-sandesh-email-service\assets"
$white = Join-Path $Src "sandesh-icon-white.png"
if (-not (Test-Path $white)) { $white = Join-Path $Assets "sandesh-icon.png" }
foreach ($name in @("sandesh-icon.png", "sandesh-logo.png")) {
    Copy-Item -Force $white (Join-Path $Assets $name)
}
$pub = Join-Path (Split-Path -Parent $PSScriptRoot) "frontend\public"
if (Test-Path $white) {
    Copy-Item -Force $white (Join-Path $pub "sandesh-icon.png")
    Write-Host "Synced to frontend/public/sandesh-icon.png (run npm build to refresh favicon sizes)"
}
Write-Host "Synced falcon-only mark to docs/assets"
