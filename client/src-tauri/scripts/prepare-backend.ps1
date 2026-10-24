# 为 Tauri 打包暂存后端自包含运行时(作为 bundle resources)
# 产出: client/src-tauri/resources/backend/{app,runtime,static,data}
# 用法:
#   powershell -ExecutionPolicy Bypass -File client\src-tauri\scripts\prepare-backend.ps1          # 已存在则跳过
#   powershell ... -Force                                                                        # 强制重建
# 环境变量 TAURI_SKIP_BACKEND=1 时直接跳过(纯前端调试)
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$here   = $PSScriptRoot
$target = Join-Path $here "..\resources\backend"

if ($env:TAURI_SKIP_BACKEND -eq "1") {
    Write-Host "== TAURI_SKIP_BACKEND=1,跳过后端暂存"
    exit 0
}

if ((Test-Path (Join-Path $target "runtime\python.exe")) -and -not $Force) {
    Write-Host "== 后端运行时已暂存: $target(用 -Force 重建)"
    exit 0
}

# site-packages 嵌套路径常超 260 字符,Remove-Item 会失败,用 robocopy 清空
function Clear-PathLong([string]$path) {
    if (-not (Test-Path $path)) { return }
    $empty = Join-Path ([System.IO.Path]::GetTempPath()) ("empty-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $empty | Out-Null
    $null = robocopy $empty $path /MIR /NFL /NDL /NJH /NJS /NP
    Remove-Item -Recurse -Force $empty -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
    if (Test-Path $path) { Write-Error "无法清空 $path" }
}

Clear-PathLong $target

Write-Host "== 暂存后端运行时到 $target"
& (Join-Path $here "..\..\..\backend\scripts\build_release.ps1") -Stage $target
if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $target "runtime\python.exe"))) {
    Write-Error "后端暂存失败(需先建好 backend\.venv 并执行过 client 构建)"
}
Write-Host "== 后端暂存完成"
