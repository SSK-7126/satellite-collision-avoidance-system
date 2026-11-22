# ICPS Satellite Avoidance — Build & Packaging Report

**Project:** Autonomous Satellite Collision Avoidance Demonstration (ICPS)
**Target Platform:** Windows 64-bit (`Win64` / `x64`)
**Build Configuration:** `Shipping`
**Engine Version:** Unreal Engine 5.7.4 (`5.7.4-0+UE5`)
**Date of Build:** 2026-11-22
**Build Outcome:** **SUCCESSFUL** (Exit Code `0`)

---

## 1. Build Environment & Toolchain Specifications

| Component | Detected Version / Path | Details |
|:---|:---|:---|
| **Operating System** | Microsoft Windows 11 / 10 x64 | Host environment for build & staging |
| **Unreal Engine** | `5.7.4` | `C:\Program Files\Epic Games\UE_5.7` |
| **UnrealBuildTool (UBT)** | `5.7.4.0` | UE5 native build automation tool |
| **Unreal Automation Tool (UAT)** | `RunUAT.bat` (`Engine\Build\BatchFiles\RunUAT.bat`) | Full pipeline automation orchestrator |
| **C++ Compiler (MSVC)** | MSVC `14.50.35717` (VS Build Tools 2026) | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.42.34433\` |
| **Windows SDK** | `10.0.26100.0` | Standard Win64 Windows Platform SDK |
| **.NET Framework SDK** | `NETFXSDK 4.6.2` | Configured via `Engine\Extras\AutoSDK\HostWin64\Win64\Windows Kits\NETFXSDK\4.6.2` |
| **Target Build Architecture** | x64 (AMD64 / Intel 64) | 64-bit native Windows executable |
| **Target Configuration** | `Shipping` | Stripped editor symbols, optimized runtime performance |

---

## 2. Packaging Pipeline & Command Line

The build and packaging pipeline was executed using Unreal Automation Tool (`RunUAT.bat BuildCookRun`) targeting a complete standalone Shipping distribution.

### Full Execution Command:
```cmd
"C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun ^
  -project="C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject" ^
  -noP4 ^
  -platform=Win64 ^
  -clientconfig=Shipping ^
  -serverconfig=Shipping ^
  -cook ^
  -build ^
  -stage ^
  -pak ^
  -iostore ^
  -package ^
  -archive ^
  -archivedirectory="C:\Users\Sriram Krovi\satellite-collision-avoidance-system\Project_Deliverables\Windows_Package\Packaged" ^
  -prereqs ^
  -nodebuginfo ^
  -utf8output
```

### Automation Pipeline Stages Executed:
1. **Target Build (UBT):**
   - Target: `SatelliteAvoidance Win64 Shipping`
   - Compiled C++ modules: `SatelliteAvoidance` game module linked with monolithic precompiled UE5 engine modules.
   - Output binary: `SatelliteAvoidance-Win64-Shipping.exe` (SHA256: `73E84CC1046D45ECF7B5117FFF537082A82411FEDBF8D8E787C626ACE55970BB`).
2. **Asset Cooking (CookCommandlet):**
   - Target level: `/Game/Scenarios/CollisionAvoidanceDemo`
   - Explicitly cooked maps: `CollisionAvoidanceDemo.umap`
   - Asset format: Platform-specific cooked binary assets with optimized shaders and materials.
3. **Packaging & Compression (Pak & IoStore):**
   - Zen IoStore container generation: `SatelliteAvoidance-Windows.ucas` and `SatelliteAvoidance-Windows.utoc`.
   - Asset index package: `SatelliteAvoidance-Windows.pak`.
4. **Staging & Archiving:**
   - Monolithic staged output copied to `Project_Deliverables\Windows_Package\Packaged\Windows\`.
   - Standalone application launcher `SatelliteAvoidance.exe` placed at root.
   - Non-UFS external data staged to `SatelliteAvoidance\Content\Data\unreal_simulation_payload.json`.

---

## 3. Build & Packaging Log Summary

- **Total Execution Duration:** 111.95 seconds (~1 min 52 sec)
- **Exit Code:** `0` (Success)
- **Compilation Errors:** `0`
- **Fatal Packaging Errors:** `0`
- **Compiler Warnings:** Minor SDK and deprecation warnings in engine header files; 0 critical warnings in project code.
- **Log Files Stored:**
  - Build Log: `[Project_Deliverables/Windows_Package/Logs/Build.log](file:///C:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Windows_Package/Logs/Build.log)`
  - Packaging Log: `[Project_Deliverables/Windows_Package/Logs/Packaging.log](file:///C:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Windows_Package/Logs/Packaging.log)`

---

## 4. Key Configuration Changes & Resolved Issues

Prior to packaging, two critical issues were resolved to ensure 100% compliant Shipping compilation:

1. **Non-Editor Actor Identification (`GetActorLabel()` Removal):**
   - **Issue:** `AActor::GetActorLabel()` is an Editor-only API (`WITH_EDITOR`) and caused compile error `C2039: 'GetActorLabel': is not a member of 'AActor'` during Shipping target compilation.
   - **Resolution:** Updated `OrbitSimulationManager.cpp` with dual-mode camera matching:
     - Under Editor (`#if WITH_EDITOR`): Matches actor label.
     - Under Shipping: Matches `Actor->Tags` and `Actor->GetName()`, with a deterministic 6-element index mapping fallback for the 6 standard cinematic cameras (`Camera_Earth_Overview`, `Camera_Satellite_Detail`, `Camera_Encounter_Overview`, `Camera_Conjunction_TCA`, `Camera_Manoeuvre_Burn`).
2. **Exclusion of Editor-Only Python Scripting:**
   - **Issue:** `PythonScriptPlugin` is an Editor tool that cannot be packaged into a standalone Shipping client.
   - **Resolution:** Restricted plugin target scope to Editor by adding `"TargetAllowList": ["Editor"]` in `SatelliteAvoidance.uproject`.
3. **Data Staging Configuration:**
   - Added `+DirectoriesToAlwaysStageAsNonUFS=(Path="Data")` to `DefaultGame.ini` to guarantee that the authoritative JSON payload is always copied into packaged builds.

---

## 5. Output Deliverables Breakdown

| File / Folder | Type | Size | Description |
|:---|:---|:---:|:---|
| `Packaged\Windows\` | Directory | 467.56 MB | Complete uncompressed standalone packaged application |
| `Packaged\Windows\SatelliteAvoidance.exe` | Executable | 589 KB | Standalone root launcher |
| `Packaged\Windows\SatelliteAvoidance\Binaries\Win64\SatelliteAvoidance-Win64-Shipping.exe` | Executable | 99.8 MB | Core native Shipping binary |
| `Packaged\Windows\SatelliteAvoidance\Content\Paks\` | Data Container | 321.4 MB | Cooked IoStore container (`.ucas`, `.utoc`, `.pak`) |
| `Packaged\Windows\SatelliteAvoidance\Content\Data\unreal_simulation_payload.json` | JSON Data | 145 KB | Authoritative scientific simulation payload (SHA256 verified) |
| `SatelliteAvoidance_Windows_Shipping_x64.zip` | ZIP Archive | 344.28 MB | Standalone distributable release archive |

---

## 6. Build Conclusion

The build was completed cleanly with zero unresolved dependencies or missing assets. The application is completely decoupled from the local Unreal Editor and development directory paths.
