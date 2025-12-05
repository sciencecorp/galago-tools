# Build all tool drivers with 32-bit Python for Electron Desktop App
# 
# REQUIREMENTS:
# - Python 3.9 32-bit installed (from python.org Windows x86 installer)
# - Adjust $Python32 path below if installed elsewhere
#
# USAGE:
#   .\scripts\build_tools.ps1                    # Build all tools
#   .\scripts\build_tools.ps1 -Tools pf400,bravo # Build specific tools
#   .\scripts\build_tools.ps1 -Clean             # Clean before build

param(
    [string]$Python32 = "C:\Python39-32\python.exe",
    [string[]]$Tools = @(),
    [switch]$Clean,
    [switch]$SkipVenv,
    [string]$OutputDir = "dist\tools"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# All available tools
$AllTools = @(
    "alps3000",
    "bioshake",
    "bravo",
    "cytation",
    "dataman70",
    "hamilton",
    "hig_centrifuge",
    "liconic",
    "microserve",
    "opentrons2",
    "pf400",
    "plateloc",
    "plr",
    "pyhamilton",
    "spectramax",
    "toolbox",
    "vcode",
    "vprep",
    "xpeel"
)

# Tools that require 32-bit Python (Windows COM/DLL dependencies)
$Require32Bit = @(
    "bravo",
    "hamilton",
    "hig_centrifuge",
    "plateloc",
    "pyhamilton",
    "vcode",
    "vprep"
)

# If no tools specified, build all
if ($Tools.Count -eq 0) {
    $Tools = $AllTools
}

# Verify Python exists
if (-not (Test-Path $Python32)) {
    Write-Host "ERROR: 32-bit Python not found at $Python32" -ForegroundColor Red
    Write-Host "Please install Python 3.9 32-bit from python.org" -ForegroundColor Yellow
    Write-Host "Or specify the path with -Python32 parameter" -ForegroundColor Yellow
    exit 1
}

# Verify Python is 32-bit
$pythonArch = & $Python32 -c "import struct; print(struct.calcsize('P') * 8)"
if ($pythonArch -ne "32") {
    Write-Host "WARNING: Python at $Python32 is $pythonArch-bit, not 32-bit" -ForegroundColor Yellow
    Write-Host "Some tools may not work correctly with 64-bit Python" -ForegroundColor Yellow
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Galago Tools Builder for Electron Desktop" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Python: $Python32 ($pythonArch-bit)" -ForegroundColor Gray
Write-Host "Tools to build: $($Tools -join ', ')" -ForegroundColor Gray
Write-Host ""

# Generate gRPC interfaces first
Write-Host "Generating gRPC interfaces..." -ForegroundColor Yellow
Set-Location $ProjectRoot
& $Python32 -m pip install grpcio-tools --quiet 2>$null
& $Python32 setup.py build_py --build-lib . 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not generate gRPC interfaces. They may already exist." -ForegroundColor Yellow
}

# Create output directory
$OutputPath = Join-Path $ProjectRoot $OutputDir
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

# Track results
$results = @{}

foreach ($tool in $Tools) {
    $toolDir = Join-Path $ProjectRoot "tools\$tool"
    $specFile = Join-Path $toolDir "$tool.spec"
    
    if (-not (Test-Path $specFile)) {
        Write-Host "SKIP: $tool - spec file not found" -ForegroundColor Yellow
        $results[$tool] = "SKIPPED"
        continue
    }
    
    Write-Host ""
    Write-Host "Building $tool..." -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    
    try {
        Set-Location $toolDir
        
        # Create virtual environment if not skipping
        if (-not $SkipVenv) {
            $venvPath = Join-Path $toolDir "venv32"
            
            if ($Clean -and (Test-Path $venvPath)) {
                Write-Host "  Cleaning existing venv..." -ForegroundColor Gray
                Remove-Item -Recurse -Force $venvPath
            }
            
            if (-not (Test-Path $venvPath)) {
                Write-Host "  Creating virtual environment..." -ForegroundColor Gray
                & $Python32 -m venv $venvPath
            }
            
            # Activate venv
            $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
            . $activateScript
            
            # Install dependencies
            Write-Host "  Installing dependencies..." -ForegroundColor Gray
            & pip install --quiet --upgrade pip
            & pip install --quiet pyinstaller grpcio grpcio-reflection protobuf pydantic
            
            # Install tool-specific dependencies
            $reqFile = Join-Path $toolDir "requirements.txt"
            if (Test-Path $reqFile) {
                & pip install --quiet -r $reqFile
            }
            
            # Install common requirements
            $commonReq = Join-Path $ProjectRoot "requirements.txt"
            if (Test-Path $commonReq) {
                & pip install --quiet -r $commonReq 2>$null
            }
        }
        
        # Clean previous build
        if ($Clean) {
            $buildDir = Join-Path $toolDir "build"
            $distDir = Join-Path $toolDir "dist"
            if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
            if (Test-Path $distDir) { Remove-Item -Recurse -Force $distDir }
        }
        
        # Run PyInstaller
        Write-Host "  Running PyInstaller..." -ForegroundColor Gray
        & pyinstaller $specFile --clean --noconfirm 2>&1 | ForEach-Object {
            if ($_ -match "error|warning" -and $_ -notmatch "UPX") {
                Write-Host "    $_" -ForegroundColor Yellow
            }
        }
        
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller failed with exit code $LASTEXITCODE"
        }
        
        # Copy to output directory
        $builtDir = Join-Path $toolDir "dist\$tool"
        if (Test-Path $builtDir) {
            $destDir = Join-Path $OutputPath $tool
            if (Test-Path $destDir) { Remove-Item -Recurse -Force $destDir }
            Copy-Item -Path $builtDir -Destination $destDir -Recurse
            Write-Host "  SUCCESS: Built to $destDir" -ForegroundColor Green
            $results[$tool] = "SUCCESS"
        } else {
            throw "Build output not found at $builtDir"
        }
        
        # Deactivate venv
        if (-not $SkipVenv) {
            deactivate
        }
        
    } catch {
        Write-Host "  FAILED: $_" -ForegroundColor Red
        $results[$tool] = "FAILED: $_"
    }
}

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Build Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$successCount = ($results.Values | Where-Object { $_ -eq "SUCCESS" }).Count
$failedCount = ($results.Values | Where-Object { $_ -like "FAILED*" }).Count
$skippedCount = ($results.Values | Where-Object { $_ -eq "SKIPPED" }).Count

foreach ($tool in $results.Keys | Sort-Object) {
    $status = $results[$tool]
    $color = switch -Wildcard ($status) {
        "SUCCESS" { "Green" }
        "FAILED*" { "Red" }
        "SKIPPED" { "Yellow" }
        default { "Gray" }
    }
    Write-Host "  $tool : $status" -ForegroundColor $color
}

Write-Host ""
Write-Host "Total: $successCount succeeded, $failedCount failed, $skippedCount skipped" -ForegroundColor Cyan
Write-Host "Output directory: $OutputPath" -ForegroundColor Gray

if ($failedCount -gt 0) {
    exit 1
}

