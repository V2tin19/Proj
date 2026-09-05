# AI Resume Server - Windows 离线安装
# 用法(管理员 PowerShell): .\install.ps1 [-InstallDir C:\ai-resume] [-Port 8000]
param(
    [string]$InstallDir = "C:\ai-resume",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$src = $PSScriptRoot

if (-not (Test-Path (Join-Path $src "runtime\python.exe"))) {
    Write-Error "未找到 runtime\python.exe,请在解压后的发行包根目录的 deploy 目录内执行"
}
if (-not (Test-Path (Join-Path $src "..\app\main.py"))) {
    Write-Error "发行包不完整(缺少 app\ 或 static\)"
}

Write-Host "== 安装到 $InstallDir =="
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Recurse -Force (Join-Path $src "..\app")     (Join-Path $InstallDir "app")
Copy-Item -Recurse -Force (Join-Path $src "..\static")  (Join-Path $InstallDir "static")
Copy-Item -Recurse -Force (Join-Path $src "..\runtime") (Join-Path $InstallDir "runtime")
Copy-Item -Recurse -Force (Join-Path $src "..\data")    (Join-Path $InstallDir "data")
if (Test-Path (Join-Path $src "..\.env")) {
    Copy-Item -Force (Join-Path $src "..\.env") (Join-Path $InstallDir ".env")
} else {
    Copy-Item -Force (Join-Path $src "..\.env.example") (Join-Path $InstallDir ".env")
    Write-Host ">> 已生成 $InstallDir\.env,请编辑填入 LLM_API_URL / LLM_API_KEY(可选 ACCESS_CODE)"
}

# 注册为 Windows 计划任务(开机自启 + 崩溃重启)
$taskName = "AIResumeServer"
$action = New-ScheduledTaskAction -Execute (Join-Path $InstallDir "deploy\start.bat") `
          -WorkingDirectory $InstallDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
            -ExecutionTimeLimit (New-TimeSpan -Days 3650) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName $taskName

Start-Sleep -Seconds 3
Write-Host "== 回环健康检查 =="
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 5
    Write-Host ($health | ConvertTo-Json -Compress)
} catch {
    Write-Warning "健康检查失败,请查看 start.bat 输出或端口占用"
}
Write-Host "== 完成! 访问 http://<本机IP>:$Port =="
Write-Host "   常用: Start-ScheduledTask/Stop-ScheduledTask -TaskName $taskName"
