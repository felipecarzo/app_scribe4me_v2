/// Registro e gerenciamento de global shortcuts.
///
/// Usa tauri-plugin-global-shortcut para registrar atalhos globais.
/// Os atalhos disparam acoes no sidecar (start/stop/cancel recording).

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use once_cell::sync::Lazy;
use tauri::{AppHandle, Manager};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};

use crate::sidecar::SidecarManager;

/// Current hotkey config — updated on re-registration.
#[derive(Clone)]
pub struct HotkeyConfig {
    pub ptt:    String,
    pub toggle: String,
    pub cancel: String,
    pub quit:   String,
}

impl Default for HotkeyConfig {
    fn default() -> Self {
        Self {
            ptt:    "Ctrl+Alt+H".into(),
            toggle: "Ctrl+Alt+T".into(),
            cancel: "Ctrl+Alt+C".into(),
            quit:   "Ctrl+Q".into(),
        }
    }
}

/// Global hotkey config (shared with the registered closure).
static HOTKEY_CONFIG: Lazy<Mutex<HotkeyConfig>> = Lazy::new(|| Mutex::new(HotkeyConfig::default()));

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

/// Register all global shortcuts with default config.
pub fn register_shortcuts(app: &AppHandle) -> Result<(), String> {
    let cfg = HotkeyConfig::default();
    register_with_config(app, cfg)
}

/// Re-register shortcuts with new config.
pub fn reregister_shortcuts(
    app: &AppHandle,
    ptt: &str,
    toggle: &str,
    cancel: &str,
    quit: &str,
) -> Result<(), String> {
    // Unregister all current shortcuts
    app.global_shortcut()
        .unregister_all()
        .map_err(|e| format!("Failed to unregister shortcuts: {e}"))?;

    let cfg = HotkeyConfig {
        ptt:    ptt.to_string(),
        toggle: toggle.to_string(),
        cancel: cancel.to_string(),
        quit:   quit.to_string(),
    };
    register_with_config(app, cfg)
}

fn register_with_config(app: &AppHandle, cfg: HotkeyConfig) -> Result<(), String> {
    // Update global config so the closure can read current values
    match HOTKEY_CONFIG.lock() {
        Ok(mut guard) => *guard = cfg.clone(),
        Err(e) => {
            log::error!("HOTKEY_CONFIG lock poisoned — shortcuts will use stale config: {e}");
        }
    }

    let ptt:    Shortcut = cfg.ptt.parse().map_err(|e| format!("Invalid PTT shortcut: {e}"))?;
    let toggle: Shortcut = cfg.toggle.parse().map_err(|e| format!("Invalid toggle shortcut: {e}"))?;
    let cancel: Shortcut = cfg.cancel.parse().map_err(|e| format!("Invalid cancel shortcut: {e}"))?;
    let quit:   Shortcut = cfg.quit.parse().map_err(|e| format!("Invalid quit shortcut: {e}"))?;

    let app_handle = app.clone();

    app.global_shortcut()
        .on_shortcuts([ptt, toggle, cancel, quit], move |_app, shortcut, event| {
            let shortcut_str = shortcut.to_string();
            let current = match HOTKEY_CONFIG.lock() {
                Ok(g) => g.clone(),
                Err(e) => {
                    log::error!("HOTKEY_CONFIG lock poisoned in shortcut handler: {e}");
                    return;
                }
            };

            // PTT: start on press, stop on release
            if shortcut_str == current.ptt {
                match event.state {
                    ShortcutState::Pressed  => handle_start(&app_handle),
                    ShortcutState::Released => handle_stop(&app_handle),
                }
                return;
            }

            // Other shortcuts: only on press
            if event.state != ShortcutState::Pressed {
                return;
            }

            if shortcut_str == current.toggle {
                handle_toggle(&app_handle);
            } else if shortcut_str == current.cancel {
                handle_cancel(&app_handle);
            } else if shortcut_str == current.quit {
                app_handle.exit(0);
            }
        })
        .map_err(|e| format!("Failed to register shortcuts: {e}"))?;

    log::info!(
        "Global shortcuts registered: PTT={}, Toggle={}, Cancel={}, Quit={}",
        cfg.ptt, cfg.toggle, cfg.cancel, cfg.quit
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
