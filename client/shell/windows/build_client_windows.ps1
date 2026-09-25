# Windows 客户端打包骨架
# 需在一台 Windows 机器执行;步骤 1 首次联网安装依赖(可缓存离线重放)
# 产出: dist-release\ai-resume-client-windows-x64-<version>.zip
param(
    [string]$Version = "1.0.0",
    [string]$Out = "..\..\dist-release"
)
$ErrorActionPreference = "Stop"
$shellDir = $PSScriptRoot
$work = Join-Path ([System.IO.Path]::GetTempPath()) "ai-resume-client-win"

Write-Host "== 1) 依赖(PyQt6,首次需联网;wheels 可缓存离线重放) =="
python -m pip download PyQt6 PyQt6-WebEngine -d "$shellDir\wheels" --quiet
python -m venv "$work\venv"
& "$work\venv\Scripts\python.exe" -m pip install --no-index --find-links "$shellDir\wheels" PyQt6 PyQt6-WebEngine --quiet

Write-Host "== 2) 组装便携目录 =="
$stage = Join-Path $work "ai-resume-client-windows-x64-$Version"
New-Item -ItemType Directory -Force -Path "$stage" | Out-Null
Copy-Item "$shellDir\..\ai_resume_client.py" "$stage\"
Copy-Item -Recurse "$shellDir\..\..\dist" "$stage\static"
# TODO(打包精修): 换用 python.org embeddable 包 + 拷贝 venv 的 PyQt6/Qt6 运行库,
# 使目标机无需安装 Python;当前骨架要求目标机已有 Python 3.11+。
Write-Warning "骨架版:目标机需已安装 Python;embeddable 精打包待完成"

Write-Host "== 3) 启动器与压缩 =="
@'
@echo off
cd /d "%~dp0"
set PYTHONHOME=
start "" pythonw ai_resume_client.py %*
'@ | Set-Content "$stage\AI简历生成器.bat" -Encoding UTF8
Compress-Archive -Path $stage -DestinationPath (Join-Path $Out "ai-resume-client-windows-x64-$Version.zip") -Force
Write-Host "== 完成: $Out\ai-resume-client-windows-x64-$Version.zip =="
