/// Registro e gerenciamento de global shortcuts.
///
/// Usa tauri-plugin-global-shortcut para registrar atalhos globais.
/// Os atalhos disparam acoes no sidecar (start/stop/cancel recording).

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use tauri::{AppHandle, Manager};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};

use crate::sidecar::SidecarManager;

/// Default hotkey strings (Tauri format).
/// These match the defaults in sidecar/config.py DEFAULT_HOTKEYS.
const DEFAULT_PTT: &str = "Ctrl+Alt+H";
const DEFAULT_TOGGLE: &str = "Ctrl+Alt+T";
const DEFAULT_CANCEL: &str = "Ctrl+Alt+C";
const DEFAULT_QUIT: &str = "Ctrl+Q";

/// Shared recording state — used by hotkeys and tray menu to decide start vs stop.
static IS_RECORDING: AtomicBool = AtomicBool::new(false);

/// Check if currently recording.
pub fn is_recording() -> bool {
    IS_RECORDING.load(Ordering::SeqCst)
}

/// Set recording state (called from lib.rs when sidecar reports status_change).
pub fn set_recording(recording: bool) {
    IS_RECORDING.store(recording, Ordering::SeqCst);
}

/// Register all global shortcuts.
pub fn register_shortcuts(app: &AppHandle) -> Result<(), String> {
    let ptt: Shortcut = DEFAULT_PTT.parse().map_err(|e| format!("Invalid PTT shortcut: {e}"))?;
    let toggle: Shortcut = DEFAULT_TOGGLE.parse().map_err(|e| format!("Invalid toggle shortcut: {e}"))?;
    let cancel: Shortcut = DEFAULT_CANCEL.parse().map_err(|e| format!("Invalid cancel shortcut: {e}"))?;
    let quit: Shortcut = DEFAULT_QUIT.parse().map_err(|e| format!("Invalid quit shortcut: {e}"))?;

    let app_handle = app.clone();

    app.global_shortcut().on_shortcuts(
        [ptt, toggle, cancel, quit],
        move |_app, shortcut, event| {
            let shortcut_str = shortcut.to_string();

            // PTT: start on press, stop on release
            if shortcut_str == DEFAULT_PTT {
                match event.state {
                    ShortcutState::Pressed => handle_start(&app_handle),
                    ShortcutState::Released => handle_stop(&app_handle),
                }
                return;
            }

            // All other shortcuts: only act on press
            if event.state != ShortcutState::Pressed {
                return;
            }

            log::info!("Shortcut pressed: {shortcut_str}");

            if shortcut_str == DEFAULT_TOGGLE {
                handle_toggle(&app_handle);
            } else if shortcut_str == DEFAULT_CANCEL {
                handle_cancel(&app_handle);
            } else if shortcut_str == DEFAULT_QUIT {
                app_handle.exit(0);
            }
        },
    ).map_err(|e| format!("Failed to register shortcuts: {e}"))?;

    log::info!(
        "Global shortcuts registered: PTT={DEFAULT_PTT}, Toggle={DEFAULT_TOGGLE}, Cancel={DEFAULT_CANCEL}, Quit={DEFAULT_QUIT}"
    );

    Ok(())
}

/// Start recording via sidecar.
fn handle_start(app: &AppHandle) {
    if is_recording() {
        return;
    }
    let sidecar = app.state::<Arc<SidecarManager>>();
    let _ = sidecar.send_request("start_recording", serde_json::json!({}));
}

/// Stop recording via sidecar.
fn handle_stop(app: &AppHandle) {
    if !is_recording() {
        return;
    }
    let sidecar = app.state::<Arc<SidecarManager>>();
    let _ = sidecar.send_request("stop_recording", serde_json::json!({}));
}

/// Toggle: start or stop recording based on current state.
fn handle_toggle(app: &AppHandle) {
    if is_recording() {
        handle_stop(app);
    } else {
        handle_start(app);
    }
}

/// Cancel: cancel current recording.
fn handle_cancel(app: &AppHandle) {
    let sidecar = app.state::<Arc<SidecarManager>>();
    let _ = sidecar.send_request("cancel_recording", serde_json::json!({}));
}
