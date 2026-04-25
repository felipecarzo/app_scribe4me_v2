/// Gerenciamento do sidecar Python.
///
/// O sidecar e um processo Python que roda como filho do Tauri.
/// Comunicacao via stdin/stdout usando JSON lines (uma msg JSON por linha).
///
/// Em dev mode: `python sidecar/sidecar_main.py`
/// Em producao: `sidecar/scribe4me-sidecar.exe` (PyInstaller binary)

use std::collections::HashMap;
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;

use serde::Serialize;
use tokio::sync::oneshot;

// --- JSON-RPC protocol types ---

#[derive(Debug, Serialize)]
pub struct RpcRequest {
    pub id: u64,
    pub method: String,
    pub params: serde_json::Value,
}

// --- SidecarManager ---

type PendingMap = Arc<Mutex<HashMap<u64, oneshot::Sender<Result<serde_json::Value, String>>>>>;

pub struct SidecarManager {
    child: Mutex<Option<Child>>,
    stdin_writer: Mutex<Option<std::process::ChildStdin>>,
    pending: PendingMap,
    next_id: Mutex<u64>,
}

impl SidecarManager {
    pub fn new() -> Self {
        Self {
            child: Mutex::new(None),
            stdin_writer: Mutex::new(None),
            pending: Arc::new(Mutex::new(HashMap::new())),
            next_id: Mutex::new(1),
        }
    }

    /// Spawn the Python sidecar process.
    ///
    /// `cmd` deve ter program + args ja configurados (sem stdin/stdout/stderr).
    /// Em dev: `Command::new("python").arg("sidecar/sidecar_main.py")`
    /// Em release: `Command::new("{resource_dir}/scribe4me-sidecar/scribe4me-sidecar[.exe]")`
    ///
    /// `event_callback` e chamado para cada evento do sidecar (thread background).
    pub fn spawn<F>(&self, mut cmd: Command, event_callback: F) -> Result<(), String>
    where
        F: Fn(String, serde_json::Value) + Send + 'static,
    {
        log::info!("Spawning sidecar: {:?}", cmd);

        eprintln!("[Tauri] Spawning sidecar: {:?}", cmd);

        let mut child = cmd
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn sidecar: {e}"))?;

        let stdout = child
            .stdout
            .take()
            .ok_or("Failed to capture sidecar stdout")?;
        let stderr = child
            .stderr
            .take()
            .ok_or("Failed to capture sidecar stderr")?;
        let stdin = child
            .stdin
            .take()
            .ok_or("Failed to capture sidecar stdin")?;

        *self.stdin_writer.lock().unwrap() = Some(stdin);
        *self.child.lock().unwrap() = Some(child);

        // Spawn stdout reader thread
        let pending = Arc::clone(&self.pending);
        thread::spawn(move || {
            let reader = BufReader::new(stdout);
            for line in reader.lines() {
                let line = match line {
                    Ok(l) => l,
                    Err(e) => {
                        log::error!("Sidecar stdout read error: {e}");
                        break;
                    }
                };

                if line.trim().is_empty() {
                    continue;
                }

                // Try to parse as JSON
                let value: serde_json::Value = match serde_json::from_str(&line) {
                    Ok(v) => v,
                    Err(e) => {
                        log::warn!("Sidecar sent invalid JSON: {e} — {line}");
                        continue;
                    }
                };

                // Check if it's a response (has "id" field)
                if let Some(id) = value.get("id").and_then(|v| v.as_u64()) {
                    let mut map = pending.lock().unwrap();
                    if let Some(sender) = map.remove(&id) {
                        if let Some(err) = value.get("error").and_then(|v| v.as_str()) {
                            let _ = sender.send(Err(err.to_string()));
                        } else {
                            let result = value
                                .get("result")
                                .cloned()
                                .unwrap_or(serde_json::Value::Null);
                            let _ = sender.send(Ok(result));
                        }
                    }
                }
                // Check if it's an event (has "event" field)
                else if let Some(event_name) = value.get("event").and_then(|v| v.as_str()) {
                    let data = value
                        .get("data")
                        .cloned()
                        .unwrap_or(serde_json::Value::Null);
                    event_callback(event_name.to_string(), data);
                }
            }
            log::info!("Sidecar stdout reader thread exiting");
        });

        // Thread que redireciona stderr do Python para o terminal do Tauri
        thread::spawn(move || {
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                if let Ok(line) = line {
                    eprintln!("[sidecar] {line}");
                }
            }
        });

        Ok(())
    }

    /// Send a JSON-RPC request and get a channel receiver for the response.
    pub fn send_request(
        &self,
        method: &str,
        params: serde_json::Value,
    ) -> Result<oneshot::Receiver<Result<serde_json::Value, String>>, String> {
        let id = {
            let mut next = self.next_id.lock().unwrap();
            let id = *next;
            *next += 1;
            id
        };

        let request = RpcRequest {
            id,
            method: method.to_string(),
            params,
        };

        let json_line = serde_json::to_string(&request)
            .map_err(|e| format!("Failed to serialize request: {e}"))?;

        let (tx, rx) = oneshot::channel();

        {
            let mut map = self.pending.lock().unwrap();
            map.insert(id, tx);
        }

        {
            let mut writer_guard = self.stdin_writer.lock().unwrap();
            if let Some(ref mut writer) = *writer_guard {
                writeln!(writer, "{json_line}")
                    .map_err(|e| format!("Failed to write to sidecar stdin: {e}"))?;
                writer
                    .flush()
                    .map_err(|e| format!("Failed to flush sidecar stdin: {e}"))?;
            } else {
                return Err("Sidecar not running".to_string());
            }
        }

        Ok(rx)
    }

    /// Gracefully shut down the sidecar process.
    pub fn shutdown(&self) {
        // Close stdin to signal EOF to the sidecar
        *self.stdin_writer.lock().unwrap() = None;

        // Wait for process to exit, then force kill if necessary
        if let Some(mut child) = self.child.lock().unwrap().take() {
            match child.wait() {
                Ok(status) => log::info!("Sidecar exited with status: {status}"),
                Err(e) => {
                    log::warn!("Sidecar wait failed: {e}, killing...");
                    let _ = child.kill();
                }
            }
        }
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        self.shutdown();
    }
}
