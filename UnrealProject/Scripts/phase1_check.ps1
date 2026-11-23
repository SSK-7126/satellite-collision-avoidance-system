Write-Host "=== 1. Module DLL details ==="
$dll = Get-Item "UnrealProject\Binaries\Win64\UnrealEditor-SatelliteAvoidance.dll"
$dll | Select-Object FullName, LastWriteTime, Length | Format-List

Write-Host "=== 2. DLL Architecture ==="
$bytes = [System.IO.File]::ReadAllBytes($dll.FullName)
$peOffset = [System.BitConverter]::ToInt32($bytes, 0x3C)
$machine = [System.BitConverter]::ToUInt16($bytes, $peOffset + 4)
Write-Host ("Machine type: 0x{0:X4} (0x8664 = x64)" -f $machine)

Write-Host "=== 3. Target Receipt ==="
$receipt = Get-Item "UnrealProject\Binaries\Win64\SatelliteAvoidanceEditor.target"
$receipt | Select-Object FullName, LastWriteTime, Length | Format-List

Write-Host "=== 4. Modules JSON ==="
$modJson = Get-Item "UnrealProject\Binaries\Win64\UnrealEditor.modules"
Get-Content $modJson.FullName

Write-Host "=== 5. Engine Modules BuildId ==="
$engModJson = Get-Item "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.modules"
(Get-Content $engModJson.FullName | ConvertFrom-Json).BuildId

Write-Host "=== 6. Target Receipt JSON Header ==="
$rc = Get-Content $receipt.FullName | ConvertFrom-Json
[PSCustomObject]@{
    TargetName = $rc.TargetName
    Platform = $rc.Platform
    Configuration = $rc.Configuration
    BuildId = $rc.Version.BuildId
    Project = $rc.Project
} | Format-List
