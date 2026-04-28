# Use python -m pip when the pip.exe launcher is broken (wrong path).
Set-Location $PSScriptRoot
& python -m pip install -r requirements.txt
