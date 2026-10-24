// 桌面端后端管理器:启动时自动拉起内嵌后端(Tauri resources 中的自包含运行时),
// 前端经 backend_info 命令拿到地址;退出时杀掉进程树。
// 若默认端口已有健康服务(dev 场景或已启动的服务端)则直接复用,不再拉起。
use std::fs;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use serde::Serialize;
use tauri::{AppHandle, Manager, RunEvent};

const BASE_PORT: u16 = 8000;
const MAX_PORT: u16 = 8010;
const HEALTH_TIMEOUT: Duration = Duration::from_secs(30);
const PROBE_TIMEOUT: Duration = Duration::from_millis(600);

#[derive(Default)]
struct BackendState {
    url: String,
    managed: bool,
    admin_user: String,
    admin_password: String,
    child: Mutex<Option<Child>>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendInfo {
    url: String,
    managed: bool,
    admin_user: String,
    admin_password: String,
}

/// 极简 HTTP 健康探测:只关心 /api/health 是否返回 200(区分本产品与端口上的其他服务)
fn http_health_ok(port: u16) -> bool {
    let Ok(addr) = format!("127.0.0.1:{port}").parse() else {
        return false;
    };
    let Ok(mut stream) = TcpStream::connect_timeout(&addr, PROBE_TIMEOUT) else {
        return false;
    };
    let _ = stream.set_read_timeout(Some(Duration::from_secs(2)));
    let request = format!("GET /api/health HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n\r\n");
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }
    let mut buf = [0u8; 256];
    let n = stream.read(&mut buf).unwrap_or(0);
    let head = String::from_utf8_lossy(&buf[..n]);
    head.starts_with("HTTP/1.1 200") || head.starts_with("HTTP/1.0 200")
}

fn port_is_free(port: u16) -> bool {
    TcpListener::bind(("127.0.0.1", port)).is_ok()
}

/// 无外部依赖的随机口令(本机 admin 初始密码)
fn random_token() -> String {
    use std::hash::{BuildHasher, Hasher};
    let make = |salt: u64| {
        let mut h = std::collections::hash_map::RandomState::new().build_hasher();
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0);
        h.write_u64(nanos ^ salt.rotate_left(17));
        h.write_u64(u64::from(std::process::id()));
        h.finish()
    };
    format!("{:016x}{:016x}", make(1), make(2))
}

fn python_exe_name() -> &'static str {
    if cfg!(windows) { "python.exe" } else { "python3" }
}

/// 读取或首次生成内置管理员口令(明文留在用户自己的数据目录)
fn ensure_admin_credentials(data_dir: &PathBuf) -> (String, String) {
    let cred_file = data_dir.join("admin-credentials.txt");
    if let Ok(content) = fs::read_to_string(&cred_file) {
        for line in content.lines() {
            if let Some(rest) = line.strip_prefix("password=") {
                let pwd = rest.trim().to_string();
                if !pwd.is_empty() {
                    return ("admin".into(), pwd);
                }
            }
        }
    }
    let pwd = random_token();
    let _ = fs::write(
        &cred_file,
        format!("AI Resume 本机服务端内置管理员\nusername=admin\npassword={pwd}\n请妥善保管,可修改或删除本文件。\n"),
    );
    ("admin".into(), pwd)
}

fn spawn_backend(
    resources: &PathBuf,
    data_dir: &PathBuf,
    port: u16,
    admin_password: &str,
    log_path: &PathBuf,
) -> std::io::Result<Child> {
    let mut cmd = Command::new(resources.join("runtime").join(python_exe_name()));
    cmd.args(["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", &port.to_string()])
        .current_dir(resources)
        .env("HOST", "127.0.0.1")
        .env("PORT", port.to_string())
        .env("DATA_DIR", data_dir)
        .env("AUTH_MODE", "optional")
        .env("ADMIN_USERNAME", "admin")
        .env("ADMIN_PASSWORD", admin_password)
        .env("PYTHONUNBUFFERED", "1")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        // CREATE_NO_WINDOW: 不弹控制台窗口
        cmd.creation_flags(0x0800_0000);
    }

    let mut child = cmd.spawn()?;

    // 后台线程把 stdout/stderr 落盘,便于排查启动失败
    if let Some(out) = child.stdout.take() {
        let path = log_path.clone();
        std::thread::spawn(move || copy_to_log(out, path));
    }
    if let Some(err) = child.stderr.take() {
        let path = log_path.clone();
        std::thread::spawn(move || copy_to_log(err, path));
    }
    Ok(child)
}

fn copy_to_log<R: Read + Send + 'static>(mut src: R, log_path: PathBuf) {
    let mut buf = [0u8; 4096];
    loop {
        match src.read(&mut buf) {
            Ok(0) | Err(_) => break,
            Ok(n) => {
                if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(&log_path) {
                    let _ = f.write_all(&buf[..n]);
                }
            }
        }
    }
}

fn ensure_backend(app: &AppHandle) -> BackendState {
    // 1) 已有健康服务(开发后端/上次残留) → 复用,不接管
    if http_health_ok(BASE_PORT) {
        return BackendState {
            url: format!("http://127.0.0.1:{BASE_PORT}"),
            managed: false,
            ..Default::default()
        };
    }

    // 2) 找内嵌运行时;资源缺失(dev 未暂存) → 维持默认地址,前端显示离线指引
    let mut resources = app
        .path()
        .resource_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join("backend");
    // dev 模式 resource_dir 不含 bundle resources,回退到源码目录(tauri dev 可用)
    #[cfg(debug_assertions)]
    if !resources.join("runtime").join(python_exe_name()).exists() {
        let source = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources").join("backend");
        if source.join("runtime").join(python_exe_name()).exists() {
            resources = source;
        }
    }
    let python = resources.join("runtime").join(python_exe_name());
    if !python.exists() {
        eprintln!("[backend] 未找到内嵌运行时: {}", python.display());
        return BackendState {
            url: format!("http://127.0.0.1:{BASE_PORT}"),
            managed: false,
            ..Default::default()
        };
    }

    // 3) 准备数据目录与内置管理员口令
    let data_dir = app
        .path()
        .app_data_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .join("backend-data");
    if let Err(e) = fs::create_dir_all(&data_dir) {
        eprintln!("[backend] 数据目录创建失败: {e}");
    }
    let log_path = data_dir.join("backend.log");
    let (admin_user, admin_password) = ensure_admin_credentials(&data_dir);

    // 4) 选端口并拉起;bind 失败(端口被占)则递增重试
    let mut child = None;
    let mut chosen = BASE_PORT;
    for port in BASE_PORT..=MAX_PORT {
        if !port_is_free(port) {
            continue;
        }
        match spawn_backend(&resources, &data_dir, port, &admin_password, &log_path) {
            Ok(c) => {
                child = Some(c);
                chosen = port;
                break;
            }
            Err(e) => eprintln!("[backend] 端口 {port} 拉起失败: {e}"),
        }
    }
    let Some(mut child) = child else {
        return BackendState {
            url: format!("http://127.0.0.1:{BASE_PORT}"),
            managed: false,
            admin_user,
            admin_password,
            ..Default::default()
        };
    };

    // 5) 等健康就绪(最多 30s;超时不视为失败,前端健康轮询会继续观察)
    let started = Instant::now();
    while started.elapsed() < HEALTH_TIMEOUT {
        if http_health_ok(chosen) {
            break;
        }
        // 进程早退(如运行时损坏)则停止等待
        if let Ok(Some(_)) = child.try_wait() {
            eprintln!("[backend] 进程提前退出,详见 {}", log_path.display());
            break;
        }
        std::thread::sleep(Duration::from_millis(300));
    }

    BackendState {
        url: format!("http://127.0.0.1:{chosen}"),
        managed: true,
        admin_user,
        admin_password,
        child: Mutex::new(Some(child)),
    }
}

fn kill_backend(state: &BackendState) {
    if let Ok(mut guard) = state.child.lock() {
        if let Some(mut child) = guard.take() {
            #[cfg(windows)]
            {
                use std::os::windows::process::CommandExt;
                // /T 连同子进程一并结束,不弹窗
                let _ = Command::new("taskkill")
                    .args(["/PID", &child.id().to_string(), "/T", "/F"])
                    .creation_flags(0x0800_0000)
                    .status();
            }
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

#[tauri::command]
fn backend_info(state: tauri::State<BackendState>) -> BackendInfo {
    BackendInfo {
        url: state.url.clone(),
        managed: state.managed,
        admin_user: state.admin_user.clone(),
        admin_password: state.admin_password.clone(),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .setup(|app| {
            let state = ensure_backend(app.handle());
            println!("[backend] url={} managed={}", state.url, state.managed);
            app.manage(state);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![backend_info])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
            if let Some(state) = app_handle.try_state::<BackendState>() {
                kill_backend(&state);
            }
        }
    });
}
