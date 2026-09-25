# Windows 客户端(骨架,与 Linux 共用同一 PyQt6 壳)

> 状态:**骨架**。壳代码 `../ai_resume_client.py` 为跨平台 Python,可直接在
> Windows 运行;打包脚本需要在一台 Windows 机器上执行(联网安装依赖属一次性环节,
> 见 CS_MIGRATION_PLAN.md §8 网络边界)。

## 运行(开发模式)

```powershell
# Python 3.11+;一次性安装依赖
pip install PyQt6 PyQt6-WebEngine

# 用已构建的 UI 运行
$env:CLIENT_DIST = "..\dist"
python ..\ai_resume_client.py
```

## 打包(待在 Windows 机器完成)

```powershell
.\build_client_windows.ps1
# 产出: dist-release\ai-resume-client-windows-x64-<version>.zip
```

`build_client_windows.ps1` 步骤(骨架已含):
1. `python -m venv .venv && pip install PyQt6 PyQt6-WebEngine`(首次联网,可缓存 wheels 离线重放);
2. 组装便携目录:`python-embedded`(python.org embeddable 包)+ PyQt6 绑定 + Qt WebEngine 运行库 + `dist/` + 壳;
3. 生成 `AI简历生成器.exe` 启动器(pythonw + 参数)与 zip + SHA256;
4. 可选:Inno Setup / NSIS 生成安装包(工具另行安装)。

## 与 Linux 版的已知差异

- 数据目录:`%LOCALAPPDATA%\ai-resume-client`
- 无 `--no-sandbox` 需求(Windows 沙箱随 QtWebEngine 正常工作)
- Edge WebView2 方案(`pywebview`)为备选,若 QtWebEngine 打包体积不可接受再切换
