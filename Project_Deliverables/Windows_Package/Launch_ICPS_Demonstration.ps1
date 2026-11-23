<#
.SYNOPSIS
    One-Click Demonstration Launcher for ICPS Satellite Collision Avoidance System
.DESCRIPTION
    1. Checks if local KAN FastAPI microservice is already healthy on http://127.0.0.1:8000
    2. Automatically starts local KAN service if not running
    3. Waits for /api/v1/health with a 15-second bounded timeout
    4. Launches Unreal Engine 5.7.4 Standalone Shipping executable
    5. Cleans up only the background KAN daemon spawned by this script upon application exit
#>

param(
    [switch]$NoGui,
    [switch]$ForcePhysicsOnly
)

$ErrorActionPreference = "Continue"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   ICPS — SATELLITE COLLISION AVOIDANCE SYSTEM (MISSION CONTROL)      " -ForegroundColor Green
Write-Host "   Local Demonstration Launcher (Aerospace Safety & Dual-Model Gate) " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Locate Repository and Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = $null

$CandidateRoots = @(
    $ScriptDir,
    (Join-Path $ScriptDir ".."),
    (Join-Path $ScriptDir "..\.."),
    "C:\Users\Sriram Krovi\satellite-collision-avoidance-system"
)

foreach ($Cand in $CandidateRoots) {
    if (Test-Path (Join-Path $Cand "backend\KAN\api\app.py")) {
        $RepoRoot = (Resolve-Path $Cand).Path
        break
    }
}

if (-not $RepoRoot) {
    Write-Warning "[WARN] Could not find backend/KAN repository root. Searching C:\..."
    $RepoRoot = "C:\Users\Sriram Krovi\satellite-collision-avoidance-system"
}

Write-Host "[INFO] Repository Root: $RepoRoot" -ForegroundColor Gray

# 2. Locate Shipping Executable
$ExePath = $null
$CandidateExes = @(
    (Join-Path $ScriptDir "SatelliteAvoidance.exe"),
    (Join-Path $ScriptDir "SatelliteAvoidance_Windows_Shipping_x64\SatelliteAvoidance.exe"),
    (Join-Path $ScriptDir "Packaged\Windows\SatelliteAvoidance.exe"),
    (Join-Path $RepoRoot "Project_Deliverables\Windows_Package\SatelliteAvoidance_Windows_Shipping_x64\SatelliteAvoidance.exe"),
    (Join-Path $RepoRoot "Project_Deliverables\Windows_Package\Packaged\Windows\SatelliteAvoidance.exe")
)

foreach ($Cand in $CandidateExes) {
    if (Test-Path $Cand) {
        $ExePath = (Resolve-Path $Cand).Path
        break
    }
}

if (-not $ExePath) {
    Write-Error "[FATAL] SatelliteAvoidance.exe not found in expected locations!"
    exit 1
}

Write-Host "[INFO] Shipping Executable: $ExePath" -ForegroundColor Gray

# 3. KAN Backend Health Check & Launch
$HealthUrl = "http://127.0.0.1:8000/api/v1/health"
$BackendStartedByLauncher = $false
$BackendProc = $null

if ($ForcePhysicsOnly) {
    Write-Host "[MODE] -ForcePhysicsOnly specified. Skipping KAN startup." -ForegroundColor Yellow
} else {
    Write-Host "[CHECK] Checking KAN microservice on port 8000..." -NoNewline
    $IsHealthy = $false
    try {
        $resp = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($resp.status -eq "OK") {
            $IsHealthy = $true
            Write-Host " [RUNNING]" -ForegroundColor Green
            Write-Host "        Model: $($resp.model_version)" -ForegroundColor Green
        }
    } catch {
        Write-Host " [OFFLINE]" -ForegroundColor Yellow
    }

    if (-not $IsHealthy) {
        Write-Host "[INFO] Starting local KAN microservice on http://127.0.0.1:8000..." -ForegroundColor Cyan
        $BackendProc = Start-Process -FilePath "python" -ArgumentList "-m uvicorn backend.KAN.api.app:app --host 127.0.0.1 --port 8000" -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru
        $BackendStartedByLauncher = $true

        Write-Host "[WAIT] Awaiting KAN initialization (timeout: 15s)..." -NoNewline
        $Elapsed = 0
        while ($Elapsed -lt 30) {
            Start-Sleep -Milliseconds 500
            $Elapsed += 1
            try {
                $resp = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 1 -ErrorAction Stop
                if ($resp.status -eq "OK") {
                    $IsHealthy = $true
                    Write-Host " [READY in $($Elapsed*0.5)s]" -ForegroundColor Green
                    Write-Host "       Model: $($resp.model_version)" -ForegroundColor Green
                    break
                }
            } catch {
                Write-Host "." -NoNewline
            }
        }
        Write-Host ""

        if (-not $IsHealthy) {
            Write-Warning "[WARN] KAN backend startup timed out. Proceeding in PHYSICS-ONLY fallback mode."
        }
    }
}

# 4. Launch Unreal Shipping Executable
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "[LAUNCH] Starting ICPS Satellite Avoidance Application..." -ForegroundColor Green
Write-Host "         Controls: Left Drag (Orbit), Right Drag (Pan), Scroll (Zoom)" -ForegroundColor Gray
Write-Host "         Cameras:  Keys 1-6 (Presets), Space (Pause/Resume), R (Reset)" -ForegroundColor Gray
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray

$GameProc = Start-Process -FilePath $ExePath -ArgumentList "-windowed -ResX=1920 -ResY=1080" -PassThru

# 5. Monitor Session and Cleanup
Write-Host "[RUNNING] Application active (PID: $($GameProc.Id)). Waiting for exit..." -ForegroundColor Cyan
$GameProc.WaitForExit()

Write-Host "[EXIT] Application closed cleanly with exit code $($GameProc.ExitCode)." -ForegroundColor Green

# 6. Stop backend ONLY if started by this launcher
if ($BackendStartedByLauncher -and $BackendProc -and (-not $BackendProc.HasExited)) {
    Write-Host "[CLEANUP] Terminating launcher-spawned KAN daemon (PID: $($BackendProc.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $BackendProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "[CLEANUP] Done." -ForegroundColor Green
} else {
    Write-Host "[CLEANUP] Preserving pre-existing KAN backend instance." -ForegroundColor Gray
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Demonstration session completed.                                   " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
