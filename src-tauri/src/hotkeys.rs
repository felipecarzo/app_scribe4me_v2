/// Registro e gerenciamento de global shortcuts.
///
/// Usa tauri-plugin-global-shortcut para registrar atalhos globais.
/// Os atalhos disparam acoes no sidecar (start/stop/cancel recording).

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use once_cell::sync::Lazy;
use tauri::{AppHandle, Manager};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutEvent, ShortcutState};

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
        // Formato canonico Tauri v2: CommandOrControl+Alt+<Key>
        // CommandOrControl = Ctrl no Win/Linux, Cmd no macOS
        Self {
            ptt:    "CommandOrControl+Alt+H".into(),
            toggle: "CommandOrControl+Alt+T".into(),
            cancel: "CommandOrControl+Alt+C".into(),
            quit:   "CommandOrControl+Q".into(),
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

    // Normaliza formato — aceita "Ctrl" como alias canonico de "CommandOrControl"
    let normalize = |s: &str| -> String {
        s.replace("CmdOrCtrl", "CommandOrControl")
         .replace("Ctrl", "CommandOrControl")
    };
    let ptt_str    = normalize(&cfg.ptt);
    let toggle_str = normalize(&cfg.toggle);
    let cancel_str = normalize(&cfg.cancel);
    let quit_str   = normalize(&cfg.quit);

    log::debug!("[hotkeys] Parsing: PTT={} Toggle={} Cancel={} Quit={}",
        ptt_str, toggle_str, cancel_str, quit_str);

    // Registra cada shortcut individualmente — se um colidir com outro app
    // (ex: Ctrl+Alt+H ja em uso por outro programa), os demais continuam
    // registrando normalmente ao inves de falhar tudo junto.
    let mut errors = Vec::new();

    let app_h1 = app.clone();
    if let Err(e) = register_one(app, "PTT", &ptt_str, move |_app, _shortcut, event: ShortcutEvent| {
        match event.state {
            ShortcutState::Pressed  => handle_start(&app_h1),
            ShortcutState::Released => handle_stop(&app_h1),
        }
    }) {
        errors.push(e);
    }

    let app_h2 = app.clone();
    if let Err(e) = register_one(app, "Toggle", &toggle_str, move |_app, _shortcut, event: ShortcutEvent| {
        if event.state == ShortcutState::Pressed {
            handle_toggle(&app_h2);
        }
    }) {
        errors.push(e);
    }

    let app_h3 = app.clone();
    if let Err(e) = register_one(app, "Cancel", &cancel_str, move |_app, _shortcut, event: ShortcutEvent| {
        if event.state == ShortcutState::Pressed {
            handle_cancel(&app_h3);
        }
    }) {
        errors.push(e);
    }

    let app_h4 = app.clone();
    if let Err(e) = register_one(app, "Quit", &quit_str, move |_app, _shortcut, event: ShortcutEvent| {
        if event.state == ShortcutState::Pressed {
            app_h4.exit(0);
        }
    }) {
        errors.push(e);
    }

    if errors.is_empty() {
        log::info!(
            "[hotkeys] OK registered: PTT={} Toggle={} Cancel={} Quit={}",
            cfg.ptt, cfg.toggle, cfg.cancel, cfg.quit
        );
        Ok(())
    } else {
        let msg = errors.join("; ");
        log::error!("[hotkeys] Registro parcial — {msg}");
        Err(msg)
    }
}

/// Registra um unico shortcut com seu handler. Nao aborta os outros em caso de erro.
fn register_one<F>(app: &AppHandle, label: &str, shortcut_str: &str, handler: F) -> Result<(), String>
where
    F: Fn(&AppHandle, &Shortcut, ShortcutEvent) + Send + Sync + 'static,
{
    let shortcut: Shortcut = shortcut_str
        .parse()
        .map_err(|e| format!("Shortcut '{label}' invalido ({shortcut_str}): {e}"))?;

    app.global_shortcut().on_shortcut(shortcut, handler).map_err(|e| {
        log::error!("[hotkeys] FAILED to register {label} ({shortcut_str}): {e}");
        format!("{label} ({shortcut_str}) ja em uso por outro programa: {e}")
    })
}

/// Start recording via sidecar. Defensive: usa try_state para nao panic.
fn handle_start(app: &AppHandle) {
    if is_recording() {
        return;
    }
    if let Some(sidecar) = app.try_state::<Arc<SidecarManager>>() {
        let _ = sidecar.send_request("start_recording", serde_json::json!({}));
    } else {
        log::warn!("handle_start: sidecar nao registrado ainda");
    }
}

/// Stop recording via sidecar.
fn handle_stop(app: &AppHandle) {
    if !is_recording() {
        return;
    }
    if let Some(sidecar) = app.try_state::<Arc<SidecarManager>>() {
        let _ = sidecar.send_request("stop_recording", serde_json::json!({}));
    } else {
        log::warn!("handle_stop: sidecar nao registrado ainda");
    }
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
    if let Some(sidecar) = app.try_state::<Arc<SidecarManager>>() {
        let _ = sidecar.send_request("cancel_recording", serde_json::json!({}));
    } else {
        log::warn!("handle_cancel: sidecar nao registrado ainda");
    }
}
