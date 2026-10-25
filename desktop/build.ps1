# Builds the Windows desktop app into desktop\dist\ATS Resume Maker\
# and zips it to desktop\dist\ATS-Resume-Maker-windows.zip.
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File desktop\build.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $root "backend\.venv\Scripts\python.exe"

Write-Host "1/3 Building frontend..."
Push-Location (Join-Path $root "frontend")
if (-not (Test-Path node_modules)) { npm ci }
npm run build
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
Pop-Location

Write-Host "2/3 Packaging app..."
& $py -m pip install -q -r (Join-Path $root "backend\requirements.txt") -r (Join-Path $PSScriptRoot "requirements.txt")
& $py -m PyInstaller --noconfirm --clean --windowed `
    --name "ATS Resume Maker" `
    --icon (Join-Path $PSScriptRoot "icon.ico") `
    --paths (Join-Path $root "backend") `
    --add-data "$(Join-Path $root 'frontend\dist');static" `
    --collect-submodules uvicorn `
    --distpath (Join-Path $PSScriptRoot "dist") `
    --workpath (Join-Path $PSScriptRoot "build") `
    --specpath (Join-Path $PSScriptRoot "build") `
    (Join-Path $PSScriptRoot "ats_app.py")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

Write-Host "3/3 Zipping..."
$zip = Join-Path $PSScriptRoot "dist\ATS-Resume-Maker-windows.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $PSScriptRoot "dist\ATS Resume Maker") -DestinationPath $zip
Write-Host "Done: desktop\dist\ATS Resume Maker\ATS Resume Maker.exe"
Write-Host "      $zip"
