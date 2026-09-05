# AI Resume Server - Windows 自包含发行包构建(零网络)
# 在 Windows 机器(已安装 Python 3.11+ 并建好 backend\.venv、frontend\dist)上执行:
#   powershell -ExecutionPolicy Bypass -File backend\scripts\build_release.ps1            # lite
#   powershell -ExecutionPolicy Bypass -File backend\scripts\build_release.ps1 -Full      # full
# 产出: dist-release\ai-resume-server-windows-x86_64-<lite|full>.zip
param(
    [switch]$Full,
    [string]$Out = (Join-Path $PSScriptRoot "..\..\dist-release")
)

$ErrorActionPreference = "Stop"
$root    = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$backend = Join-Path $root "backend"
$venvSite = Join-Path $backend ".venv\Lib\site-packages"

if (-not (Test-Path $venvSite)) { Write-Error "未找到 $venvSite(请先 pip install -r requirements.txt)" }
if (-not (Test-Path (Join-Path $root "frontend\dist\index.html"))) { Write-Error "缺少 frontend\dist\index.html(请先 npm run build)" }

$variant = if ($Full) { "full" } else { "lite" }
$name    = "ai-resume-server-windows-x86_64-$variant"
$stage   = Join-Path ([System.IO.Path]::GetTempPath()) "$name"

Write-Host "== 构建发行包: $name =="
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path `
    "$stage\app", "$stage\static", "$stage\deploy", "$stage\data", `
    "$stage\runtime\Lib\site-packages" | Out-Null

Copy-Item -Recurse -Force (Join-Path $backend "app")     "$stage\app"
Copy-Item (Join-Path $backend "data\*.json")              "$stage\data"
Copy-Item -Recurse -Force (Join-Path $root "frontend\dist") "$stage\static"
Copy-Item -Recurse -Force (Join-Path $root "deploy")      "$stage\deploy"
Copy-Item -Force (Join-Path $root ".env.example")         "$stage\.env.example"
Copy-Item -Force (Join-Path $root "deploy\README-DEPLOY.md") "$stage\README-DEPLOY.md"

# 解释器:venv 的 python.exe + 官方安装目录的 Lib(标准库)
$pyExe = (Join-Path $backend ".venv\Scripts\python.exe")
Copy-Item $pyExe "$stage\runtime\python.exe"
$home_dir = (Split-Path (Split-Path $pyExe))   # venv\Scripts -> venv -> 由 pyvenv.cfg 读取 home
$baseHome = (Get-Content (Join-Path $backend ".venv\pyvenv.cfg") | Select-String "^home\s*=\s*(.+)$").Matches[0].Groups[1].Value.Trim()
Copy-Item -Recurse -Force (Join-Path $baseHome "Lib") "$stage\runtime\Lib"
# python3.dll / python313.dll 与 vcruntime 跟随解释器,一并拷贝
Get-ChildItem $baseHome -Filter "python*.dll" | Copy-Item -Destination "$stage\runtime"
Get-ChildItem $baseHome -Filter "vcruntime*.dll" | Copy-Item -Destination "$stage\runtime"

# site-packages
Copy-Item -Recurse -Force (Join-Path $venvSite "*") "$stage\runtime\Lib\site-packages\"

if (-not $Full) {
    Write-Host "== lite: 剔除嵌入模型栈 =="
    $exclude = "torch","torchgen","functorch","include","sentence_transformers","transformers",
               "tokenizers","safetensors","huggingface_hub","hf_xet","scipy","sklearn","sympy",
               "mpmath","networkx"
    foreach ($e in $exclude) {
        Get-ChildItem "$stage\runtime\Lib\site-packages" -Filter "$e*" -Directory |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Get-ChildItem $stage -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 自举验证
& "$stage\runtime\python.exe" -c "import fastapi, uvicorn, numpy, docx, pypdf; print('runtime OK')"

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$zip = Join-Path $Out "$name.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path $stage -DestinationPath $zip
Remove-Item -Recurse -Force $stage
Write-Host "== 完成: $zip =="
Get-Item $zip | Select-Object Name, @{n="SizeMB";e={[math]::Round($_.Length/1MB,1)}}
