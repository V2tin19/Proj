# Android 客户端(骨架)

> 状态:**骨架**。Android 无法使用 PyQt6(Qt 官方未提供 Python 绑定的 Android 支持),
> 规划路线为 **Tauri 2 WebView 壳**:复用同一套 Vue UI(`client/dist`),Rust 仅作壳。
> 工具链(JDK 17、Android SDK/NDK、Rust android targets)需一次性联网安装,
> 见 CS_MIGRATION_PLAN.md §8;搭建后所有构建可离线重复。

## 计划结构(待工具链就位后初始化)

```text
client/shell/android/
├── README.md                  # 本文件
├── build-android.sh           # 骨架:tauri android build 封装
└── tauri.conf.json.template   # 骨架:Android 打包配置模板
```

## 初始化步骤(需要工具链的机器上执行一次)

```bash
rustup target add aarch64-linux-android armv7-linux-androideabi
cargo install tauri-cli --version ^2
# Android Studio 安装 SDK/NDK,设置 ANDROID_HOME / NDK_HOME
cd client
npm install -D @tauri-apps/cli @tauri-apps/api   # 一次性
npx tauri android init                            # 生成 src-tauri/gen/android
npx tauri android build --apk                     # 产出 .apk
```

## Android 专项注意事项(承接 CS_MIGRATION_PLAN §9)

- 明文 HTTP:局域网直连服务端需 `usesCleartextTraffic=true`(debug/内网包);
- 会话令牌:WebView localStorage 已随 Tauri 持久化;如需 Keystore 级保护再引入 secure-storage 插件;
- SSE 对话:前台流式正常;后台切换由 Android 生命周期管理,UI 已有断线提示;
- 签名:生成 keystore 后口令线下保管,不入库;
- 目标:Android 10+(与计划 §Phase D 一致),高低端真机各一台验收。

## 与桌面版共用部分

- UI:同一份 `client/dist`(构建产物),注册/登录/服务端地址逻辑全部复用;
- 差异仅在外壳(桌面=PyQt6,Android=Tauri WebView)。
