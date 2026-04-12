use std::sync::Arc;

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager,
};

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

// --- App setup ---

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_notification::init())
        .setup(|app| {
            // Build tray menu
            let show_i = MenuItem::with_id(app, "show", "Configuracoes", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Sair", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_i, &quit_i])?;

            // Build tray icon
            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .tooltip("Scribe4me — Pronto")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
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

            // Event callback: forward sidecar events to the frontend via Tauri events
            let sidecar_for_spawn = Arc::clone(&sidecar);
            if let Err(e) = sidecar_for_spawn.spawn(move |event_name, data| {
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

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_app_version, sidecar_send])
        .run(tauri::generate_context!())
        .expect("error while running Scribe4me");
}
