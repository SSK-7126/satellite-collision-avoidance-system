# ICPS — Local KAN Backend Startup & Management Guide

**Service:** Kolmogorov-Arnold Network (KAN) Collision Prediction Microservice  
**Target URL:** `http://127.0.0.1:8000`  
**API Specification:** OpenAPI 3.1 (`/docs` and `/openapi.json`)  
**Host Environment:** Local Windows Laptop Python 3.11+ / PyTorch  

---

## 1. Automated Execution (Recommended)

When using the provided one-click launcher:
```powershell
powershell -ExecutionPolicy Bypass -File .\Launch_ICPS_Demonstration.ps1
```
or double-clicking:
```cmd
Launch_ICPS_Demonstration.bat
```
The launcher automatically performs health checks, launches the backend daemon if it is not running, waits for `/api/v1/health`, and shuts down only its spawned instance upon application exit.

---

## 2. Manual Startup Instructions

If you prefer to run the KAN backend in a dedicated terminal window for live log inspection:

### Step 1: Open PowerShell or Command Prompt
Navigate to the repository root directory:
```powershell
cd "C:\Users\Sriram Krovi\satellite-collision-avoidance-system"
```

### Step 2: Launch the FastAPI Uvicorn Server
```powershell
python -m uvicorn backend.KAN.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Expected terminal output:
```text
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

## 3. Service Verification & Diagnostic Endpoints

### 1. Health Probe
```powershell
curl http://127.0.0.1:8000/api/v1/health
```
Response:
```json
{
  "status": "OK",
  "service": "KAN Collision Prediction Service",
  "model_version": "pykan_esa_kelvins_v1.0",
  "timestamp_utc": "2026-11-23T08:00:00Z"
}
```

### 2. Model Metadata & B-Spline Architecture
```powershell
curl http://127.0.0.1:8000/api/v1/model-info
```
Response details:
- **Architecture:** `[33, 8, 1]` (33 input features, 8 hidden neurons, 1 output $\log_{10} P_c$)
- **Spline Order:** $k = 3$ (Cubic B-Splines)
- **Grid Intervals:** $G = 5$

---

## 4. Fallback Behavior & Error Handling

| Condition | System Response | Dashboard Indication |
| :--- | :--- | :--- |
| **Port 8000 Offline** | Unreal C++ handles connection error after bounded 2.0s timeout | Card 5 shows `[BACKEND UNAVAILABLE]`, Card 6 shows `[PHYSICS ONLY (FALLBACK)]` |
| **Missing Covariance** | Backend returns `INSUFFICIENT_INPUT_DATA` with missing feature list | Card 5 shows `[INSUFFICIENT_INPUT_DATA]`, physics continues autonomously |
| **Backend Restored** | Next step transition re-establishes HTTP connection automatically | Card 5 updates with live inference, Card 6 re-evaluates concordance gate |
| **High Latency** | Async HTTP thread pool isolates game thread | Unreal renders smoothly at 60+ FPS with zero stutter |
