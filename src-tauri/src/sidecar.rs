/// Gerenciamento do sidecar Python.
///
/// O sidecar e um executavel Python (PyInstaller) que roda como processo filho.
/// Comunicacao via stdin/stdout usando JSON lines (uma msg JSON por linha).
///
/// TODO: Fase 2 — implementar spawn do sidecar + bridge de mensagens.

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct RpcRequest {
    pub id: u64,
    pub method: String,
    pub params: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RpcResponse {
    pub id: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RpcEvent {
    pub event: String,
    pub data: serde_json::Value,
}
