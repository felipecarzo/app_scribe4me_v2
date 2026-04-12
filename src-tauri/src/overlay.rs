/// Overlay window — pill flutuante mostrada durante gravacao/transcricao.
///
/// Janela transparente, always-on-top, sem decoracoes, sem entrada na taskbar.
/// Criada sob demanda quando o sidecar reporta status recording/transcribing.

use tauri::{AppHandle, Manager, PhysicalPosition, WebviewUrl, WebviewWindowBuilder};

const OVERLAY_LABEL: &str = "overlay";
const OVERLAY_W: f64 = 440.0; // largura logica em pixels
const OVERLAY_H: f64 = 80.0;  // altura logica em pixels
const MARGIN_BOTTOM: f64 = 48.0; // margem logica acima da borda inferior (acima da taskbar)

/// Mostra o overlay se o status e recording ou transcribing; esconde nos demais.
pub fn show_or_hide(app: &AppHandle, status: &str) {
    match status {
        "recording" | "transcribing" => show(app),
        _ => hide(app),
    }
}

/// Cria ou exibe a janela overlay.
pub fn show(app: &AppHandle) {
    if let Some(w) = app.get_webview_window(OVERLAY_LABEL) {
        if let Err(e) = position_bottom_center(&w) {
            eprintln!("[overlay] Failed to position on show: {e}");
        }
        let _ = w.show();
        return;
    }

    // Determinar URL: em dev usa devUrl, em prod usa asset protocol
    let url = WebviewUrl::App("overlay.html".into());

    match WebviewWindowBuilder::new(app, OVERLAY_LABEL, url)
        .title("Scribe4me Overlay")
        .inner_size(OVERLAY_W, OVERLAY_H)
        .decorations(false)
        .transparent(true)
        .always_on_top(true)
        .skip_taskbar(true)
        .resizable(false)
        .shadow(false)
        .focused(false)
        .visible(false) // posiciona antes de mostrar
        .build()
    {
        Ok(w) => {
            // Ignora eventos de mouse para nao bloquear o usuario
            let _ = w.set_ignore_cursor_events(true);
            if let Err(e) = position_bottom_center(&w) {
                eprintln!("[overlay] Failed to position on create: {e}");
            }
            let _ = w.show();
        }
        Err(e) => eprintln!("[overlay] Failed to create overlay window: {e}"),
    }
}

/// Esconde a janela overlay (mantem-a em memoria para reuso rapido).
pub fn hide(app: &AppHandle) {
    if let Some(w) = app.get_webview_window(OVERLAY_LABEL) {
        let _ = w.hide();
    }
}

/// Posiciona a janela no centro horizontal, proximo ao fundo do monitor primario.
fn position_bottom_center(window: &tauri::WebviewWindow) -> Result<(), tauri::Error> {
    let monitor = match window.primary_monitor()? {
        Some(m) => m,
        None => return Ok(()), // nenhum monitor detectado — nao posiciona
    };

    let screen_size = monitor.size();
    let screen_pos = monitor.position();
    let scale = monitor.scale_factor();

    // Converter dimensoes logicas para fisicas
    let win_w = (OVERLAY_W * scale) as i32;
    let win_h = (OVERLAY_H * scale) as i32;
    let margin = (MARGIN_BOTTOM * scale) as i32;

    let x = screen_pos.x + (screen_size.width as i32 - win_w) / 2;
    let y = screen_pos.y + screen_size.height as i32 - win_h - margin;

    window.set_position(PhysicalPosition::new(x, y))?;
    Ok(())
}
