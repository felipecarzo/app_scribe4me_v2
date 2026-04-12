use std::sync::Arc;

use std::sync::Mutex;

use tauri::{
    menu::{Menu, MenuItem, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager,
};

/// Dynamic tray menu items that can be updated at runtime.
struct TrayMenuItems {
    status: MenuItem<tauri::Wry>,
    backend: MenuItem<tauri::Wry>,
    model: MenuItem<tauri::Wry>,
    record: MenuItem<tauri::Wry>,
}

mod hotkeys;
mod overlay;
mod sidecar;

use sidecar::SidecarManager;

// --- Tauri commands ---

#[tauri::command]
fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// Send a JSON-RPC request to the sidecar and return the result.
#[tauri::command]
async fn sidecar_send(
    method: String,
    params: serde_json::Value,
    state: tauri::State<'_, Arc<SidecarManager>>,
) -> Result<serde_json::Value, String> {
    let rx = state.send_request(&method, params)?;
    rx.await.map_err(|_| "Sidecar response channel closed".to_string())?
}

/// Update tray menu labels for backend and model.
#[tauri::command]
fn update_tray_info(
    backend: String,
    model: String,
    state: tauri::State<'_, Mutex<TrayMenuItems>>,
) {
    if let Ok(items) = state.lock() {
        let _ = items.backend.set_text(format!("Backend: {backend}"));
        let _ = items.model.set_text(format!("Modelo: {model}"));
    }
}

/// Re-register global shortcuts with new key combinations.
#[tauri::command]
fn update_shortcuts(
    ptt: String,
    toggle: String,
    cancel: String,
    quit: String,
    app: AppHandle,
) -> Result<(), String> {
    hotkeys::reregister_shortcuts(&app, &ptt, &toggle, &cancel, &quit)
}

// --- App setup ---

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            // Build tray menu with status info and actions
            let status_i = MenuItem::with_id(app, "status", "Pronto", false, None::<&str>)?;
            let backend_i = MenuItem::with_id(app, "backend", "Backend: local", false, None::<&str>)?;
            let model_i = MenuItem::with_id(app, "model", "Modelo: large-v3", false, None::<&str>)?;
            let sep1 = PredefinedMenuItem::separator(app)?;
            let record_i = MenuItem::with_id(app, "record", "Gravar (Ctrl+Alt+T)", true, None::<&str>)?;
            let cancel_i = MenuItem::with_id(app, "cancel", "Cancelar (Ctrl+Alt+C)", true, None::<&str>)?;
            let sep2 = PredefinedMenuItem::separator(app)?;
            let show_i = MenuItem::with_id(app, "show", "Configuracoes", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Sair (Ctrl+Q)", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[
                &status_i, &backend_i, &model_i, &sep1,
                &record_i, &cancel_i, &sep2,
                &show_i, &quit_i,
            ])?;

            // Store dynamic menu items for runtime updates
            let tray_items = TrayMenuItems {
                status: status_i.clone(),
                backend: backend_i.clone(),
                model: model_i.clone(),
                record: record_i.clone(),
            };
            app.manage(Mutex::new(tray_items));

            // Build tray icon
            let _tray = TrayIconBuilder::with_id("main-tray")
                .menu(&menu)
                .tooltip("Scribe4me — Pronto")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "record" => {
                        // Toggle recording via sidecar using shared state
                        if let Some(sidecar) = app.try_state::<Arc<SidecarManager>>() {
                            if hotkeys::is_recording() {
                                let _ = sidecar.send_request("stop_recording", serde_json::json!({}));
                            } else {
                                let _ = sidecar.send_request("start_recording", serde_json::json!({}));
                            }
                        }
                    }
                    "cancel" => {
                        if let Some(sidecar) = app.try_state::<Arc<SidecarManager>>() {
                            let _ = sidecar.send_request("cancel_recording", serde_json::json!({}));
                        }
                    }
                    "quit" => {
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            // Hide main window on start — app lives in tray
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.hide();
            }

            // Spawn Python sidecar
            let sidecar = Arc::new(SidecarManager::new());
            let app_handle = app.handle().clone();

            // Resolve sidecar command: dev uses python script, release uses PyInstaller binary
            let sidecar_cmd = build_sidecar_command(app)?;

            // Event callback: forward sidecar events to the frontend + update tray icon
            let sidecar_for_spawn = Arc::clone(&sidecar);
            if let Err(e) = sidecar_for_spawn.spawn(sidecar_cmd, move |event_name, data| {
                // Update tray icon and overlay on status_change
                if event_name == "status_change" {
                    if let Some(status) = data.get("status").and_then(|v| v.as_str()) {
                        update_tray_icon(&app_handle, status);
                        overlay::show_or_hide(&app_handle, status);
                    }
                }

                let payload = serde_json::json!({
                    "event": event_name,
                    "data": data,
                });
                if let Err(e) = app_handle.emit("sidecar-event", &payload) {
                    eprintln!("Failed to emit sidecar event: {e}");
                }
            }) {
                eprintln!("Failed to spawn sidecar: {e}");
                // Continue without sidecar — UI will show disconnected state
            }

            // Store sidecar manager in Tauri state for commands
            app.manage(sidecar);

            // Register global shortcuts (PTT, Toggle, Cancel, Quit)
            if let Err(e) = hotkeys::register_shortcuts(app.handle()) {
                eprintln!("Failed to register global shortcuts: {e}");
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_app_version, sidecar_send, update_tray_info, update_shortcuts])
        .run(tauri::generate_context!())
        .expect("error while running Scribe4me");
}

/// Constroi o Command para iniciar o sidecar Python.
///
/// Em debug (dev mode): executa `python {workspace}/sidecar/sidecar_main.py`
/// Em release: executa o binario PyInstaller em `{resource_dir}/scribe4me-sidecar/`
///
/// IMPORTANTE: em release, o binario deve existir no bundle. Se nao existir,
/// retorna erro descritivo. Execute `sidecar/build_sidecar.bat` antes de `tauri build`.
fn build_sidecar_command(app: &tauri::App) -> Result<std::process::Command, Box<dyn std::error::Error>> {
    #[cfg(debug_assertions)]
    {
        let _ = app; // app nao e usado em dev mode
        // Dev: sidecar Python a partir do current_dir (workspace root)
        let script = std::env::current_dir()
            .unwrap_or_default()
            .join("../sidecar/sidecar_main.py");
        let mut cmd = std::process::Command::new("python");
        cmd.arg(script);
        Ok(cmd)
    }
    #[cfg(not(debug_assertions))]
    {
        // Release: binario PyInstaller nos resources do bundle Tauri
        use tauri::Manager;
        let resource_dir = app.path().resource_dir()?;
        let exe_name = if cfg!(target_os = "windows") {
            "scribe4me-sidecar.exe"
        } else {
            "scribe4me-sidecar"
        };
        let sidecar_exe = resource_dir
            .join("scribe4me-sidecar")
            .join(exe_name);
        // Guard: falha rapido com mensagem clara se o bundle nao inclui o binario.
        // Causa mais comum: `tauri build` foi executado sem rodar `build_sidecar.bat` antes.
        if !sidecar_exe.exists() {
            return Err(format!(
                "Sidecar binary not found: {}. Run sidecar/build_sidecar.bat before tauri build.",
                sidecar_exe.display()
            ).into());
        }
        Ok(std::process::Command::new(sidecar_exe))
    }
}

/// Update tray icon and menu labels based on sidecar status.
fn update_tray_icon(app: &AppHandle, status: &str) {
    // Sync shared recording state for hotkeys and tray menu toggle
    hotkeys::set_recording(status == "recording");

    // Update menu status and record labels via managed state
    if let Some(items_state) = app.try_state::<Mutex<TrayMenuItems>>() {
        if let Ok(items) = items_state.lock() {
            let status_text = match status {
                "idle" => "Pronto",
                "loading" => "Carregando modelo...",
                "recording" => "Gravando...",
                "transcribing" => "Transcrevendo...",
                "done" => "Concluido",
                "error" => "Erro",
                _ => status,
            };
            let _ = items.status.set_text(status_text);
            let record_label = if status == "recording" {
                "Parar (Ctrl+Alt+T)"
            } else {
                "Gravar (Ctrl+Alt+T)"
            };
            let _ = items.record.set_text(record_label);
        }
    }
    let icon_png: &[u8] = match status {
        "idle" => include_bytes!("../icons/tray-idle.png"),
        "loading" => include_bytes!("../icons/tray-loading.png"),
        "recording" => include_bytes!("../icons/tray-recording.png"),
        "transcribing" => include_bytes!("../icons/tray-transcribing.png"),
        "done" => include_bytes!("../icons/tray-done.png"),
        "error" => include_bytes!("../icons/tray-error.png"),
        _ => include_bytes!("../icons/tray-idle.png"),
    };

    let tooltip = match status {
        "idle" => "Scribe4me — Pronto",
        "loading" => "Scribe4me — Carregando...",
        "recording" => "Scribe4me — Gravando",
        "transcribing" => "Scribe4me — Transcrevendo...",
        "done" => "Scribe4me — Concluido",
        "error" => "Scribe4me — Erro",
        _ => "Scribe4me",
    };

    if let Some(tray) = app.tray_by_id("main-tray") {
        if let Ok(icon) = tauri::image::Image::from_bytes(icon_png) {
            let _ = tray.set_icon(Some(icon));
        }
        let _ = tray.set_tooltip(Some(tooltip));
    }
}
