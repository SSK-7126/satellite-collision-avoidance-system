# ICPS Satellite Avoidance — Runtime Dependency Report

**Project:** Autonomous Satellite Collision Avoidance Demonstration (ICPS)
**Target Architecture:** Windows 64-bit (`Win64` / `x64`)
**Build Configuration:** `Shipping`
**Engine Version:** Unreal Engine 5.7.4
**Date of Audit:** 2026-11-22
**Dependency Audit Status:** **CLEAN (Zero External Engine/Dev Dependencies)**

---

## 1. Executive Summary

This report documents the exhaustive runtime dependency analysis performed on the packaged standalone application `SatelliteAvoidance.exe` and its native binary `SatelliteAvoidance-Win64-Shipping.exe`. The application is completely decoupled from the local Unreal Editor installation and Python development environment. All engine-specific and hardware-acceleration libraries are either statically linked or bundled directly in the distribution directory.

---

## 2. Bundled Runtime Dynamic Link Libraries (DLLs)

The packaged distribution includes all necessary vendor, graphics, audio, and multithreading runtimes. These libraries reside directly within the application tree:

| DLL Relative Path | File Size | Provider / Purpose |
|:---|:---:|:---|
| `SatelliteAvoidance\Binaries\Win64\D3D12\x64\D3D12Core.dll` | 4,544,000 B | **DirectX 12 Agility SDK Core Runtime** (Provides latest DX12 pipeline features independently of OS version) |
| `SatelliteAvoidance\Binaries\Win64\D3D12\x64\d3d12SDKLayers.dll` | 5,104,632 B | **DirectX 12 SDK Layer** (Runtime API validation and diagnostic layer) |
| `SatelliteAvoidance\Binaries\Win64\DML\x64\DirectML.dll` | 18,537,968 B | **DirectX DirectML Runtime** (Hardware-accelerated machine learning and compute evaluation) |
| `SatelliteAvoidance\Binaries\Win64\tbb12.dll` | 331,704 B | **Intel OneAPI Threading Building Blocks (TBB 2021)** (Task parallelism and CPU work-stealing scheduler) |
| `SatelliteAvoidance\Binaries\Win64\tbbmalloc.dll` | 117,688 B | **Intel TBB Scalable Memory Allocator** (High-throughput multithreaded heap manager) |
| `Engine\Plugins\NNE\NNERuntimeORT\Binaries\ThirdParty\Onnxruntime\Win64\onnxruntime.dll` | 14,692,872 B | **Microsoft ONNX Runtime** (Neural Network Engine inference library) |
| `Engine\Binaries\ThirdParty\NVIDIA\NVaftermath\Win64\GFSDK_Aftermath_Lib.x64.dll` | 5,442,592 B | **NVIDIA Aftermath Diagnostic Library** (GPU crash instrumentation and dump generation) |
| `Engine\Binaries\ThirdParty\Windows\XAudio2_9\x64\xaudio2_9redist.dll` | 858,144 B | **DirectX XAudio 2.9 Redistributable** (Low-latency spatialized audio playback) |
| `Engine\Binaries\ThirdParty\Vorbis\Win64\VS2015\libvorbis_64.dll` | 1,724,856 B | **Xiph.Org libvorbis** (Audio codec) |
| `Engine\Binaries\ThirdParty\Vorbis\Win64\VS2015\libvorbisfile_64.dll` | 48,568 B | **Xiph.Org libvorbisfile** (Streaming Ogg Vorbis decoder) |
| `Engine\Binaries\ThirdParty\Ogg\Win64\VS2015\libogg_64.dll` | 59,832 B | **Xiph.Org libogg** (Bitstream framing and container library) |
| `Engine\Binaries\ThirdParty\DbgHelp\dbghelp.dll` | 2,232,688 B | **Microsoft Debug Help** (Crash reporting and minidump generation) |
| `Engine\Binaries\ThirdParty\MsQuic\v220\win64\msquic.dll` | 2,547,080 B | **Microsoft QUIC Library** (Modern transport protocol runtime) |

---

## 3. External Operating System & Platform Dependencies

The application relies only on standard Windows system APIs and the Microsoft Visual C++ universal runtime:

### 3.1 Microsoft Visual C++ Runtime
- **Required DLLs:** `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, `MSVCP140.dll`, `MSVCP140_1.dll`
- **Minimum Version:** Visual Studio 2015–2022/2026 Runtime (v14.x)
- **Status on Target Machines:** Pre-installed on virtually all modern Windows installations; freely installable via the official redistributable installer:
  `https://aka.ms/vs/17/release/vc_redist.x64.exe`

### 3.2 Windows System DLLs (Provided by Windows OS)
- `KERNEL32.dll` / `KERNELBASE.dll`: Process, thread, and memory management.
- `USER32.dll` / `GDI32.dll`: Window creation, desktop interaction, input handling.
- `SHELL32.dll` / `SHLWAPI.dll`: Shell integration, file associations, path manipulation.
- `OLE32.dll` / `OLEAUT32.dll`: Component Object Model (COM) infrastructure.
- `ADVAPI32.dll`: Security descriptor and registry interaction.
- `WS2_32.dll`: Windows Sockets networking API.
- `D3D12.dll` / `DXGI.dll`: DirectX 12 graphics driver interface.

---

## 4. Verification of Development Decoupling

A primary objective was ensuring the application does not leak dependencies back to the development environment:

| Dependency Category | Packaged Status | Verification Evidence |
|:---|:---:|:---|
| **Unreal Editor** | **ZERO Dependency** | Compiled as `TargetType.Game` monolithic Shipping binary. No Editor modules (`UnrealEd`, `EditorStyle`, etc.) linked. Runs without `UnrealEditor.exe`. |
| **Python Environment** | **ZERO Dependency** | Scoped `PythonScriptPlugin` to Editor only (`"TargetAllowList": ["Editor"]`). Zero Python DLLs (`python3*.dll`), scripts, or virtual environments exist in package. |
| **Development Machine Paths** | **ZERO Dependency** | All data access uses relative paths via `FPaths::ProjectContentDir()`. No hardcoded laptop absolute paths (`C:\Users\Sriram Krovi\...`) are required at runtime. |
| **Development Git Repo** | **ZERO Dependency** | Standalone package runs outside the repository root. All level content is pre-cooked into `.ucas`/`.utoc` containers. |

---

## 5. Target Machine Compatibility & System Requirements

### Minimum Hardware:
- **Processor:** Intel Core i5-4460 / AMD Ryzen 3 1200 or equivalent (4 cores)
- **System Memory:** 8 GB RAM
- **GPU:** DirectX 12 compatible graphics card with Feature Level 11_0 or 12_0 (NVIDIA GTX 1050 / AMD Radeon RX 560 / Intel UHD Graphics 730 or newer)
- **Storage:** 1.0 GB available space on NTFS or exFAT drive
- **Operating System:** Windows 10 64-bit (Version 1909 or higher) or Windows 11 64-bit

### Recommended Hardware:
- **Processor:** Intel Core i7-10700K / AMD Ryzen 7 3700X or higher
- **System Memory:** 16 GB RAM
- **GPU:** NVIDIA GeForce RTX 2060 / AMD Radeon RX 6600 (6 GB+ VRAM)
- **DirectX:** Version 12 Ultimate (Feature Level 12_2)

---

## 6. Dependency Conclusion

The application bundle is self-contained. Any modern 64-bit Windows PC with standard DirectX 12 GPU drivers and the standard Microsoft Visual C++ redistributable can execute the application directly from the extracted ZIP archive without additional setup.
