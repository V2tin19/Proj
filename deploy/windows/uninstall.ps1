# AI Resume Server - Windows 卸载
param([string]$InstallDir = "C:\ai-resume")
$ErrorActionPreference = "Continue"
Stop-ScheduledTask -TaskName "AIResumeServer" -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "AIResumeServer" -Confirm:$false -ErrorAction SilentlyContinue
if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
    Write-Host "已卸载 $InstallDir"
} else {
    Write-Host "未找到安装目录 $InstallDir"
}
