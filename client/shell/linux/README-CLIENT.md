# AI 简历生成器 — Linux 客户端使用说明

三种安装形态任选其一(均需配合服务端 `ai-resume-server` 使用):

## 1. deb(Ubuntu / Debian)

```bash
sudo apt install ./ai-resume-client_1.0.0-amd64.deb
# 自动拉取依赖:python3-pyqt6、python3-pyqt6.qtwebengine
# 启动:应用菜单「AI 简历生成器」或命令行 ai-resume-client
sudo apt remove ai-resume-client   # 卸载
```

## 2. Arch / Manjaro(.pkg.tar.zst)

```bash
sudo pacman -U ai-resume-client-1.0.0-1-x86_64.pkg.tar.zst
# 依赖:python、python-pyqt6-webengine(经 pacman 自动解析)
sudo pacman -R ai-resume-client   # 卸载
```

## 3. 自包含免安装包(selfcontained tar.zst)

内嵌 Python + Qt6 运行时,**目标机零依赖、零安装**:

```bash
tar --zstd -xf ai-resume-client-linux-x86_64-selfcontained-1.0.0.tar.zst
cd ai-resume-client-linux-x86_64-1.0.0
./start-client.sh
# 可选:创建桌面入口
cp settings-desktop/ai-resume-client.desktop ~/.local/share/applications/ 2>/dev/null || true
```

## 首次使用

1. 启动后进入「注册 / 登录」页;
2. 顶部填**服务端地址**(如 `http://192.168.1.10:8000`,同机部署可留空);
3. 注册账号(或登录),即可使用全部功能;会话在本地持久化,重启免登录。

## 已知说明

- 自包含包默认以 `--no-sandbox` 启动 Chromium(tar 分发无法保留 setuid 位);
  deb/pacman 包走系统 Qt6,保留沙箱。可用环境变量 `QTWEBENGINE_CHROMIUM_FLAGS` 覆盖。
- 客户端数据(会话/设置)存于 `~/.local/share/ai-resume-client`。
- 服务端部署见仓库根 README 与 `deploy/README-DEPLOY.md`。
