/**
 * Protocolo de comunicacao com o sidecar Python via JSON-RPC sobre stdin/stdout.
 *
 * O sidecar Python e lancado pelo Tauri como processo filho.
 * Comunicacao: JSON lines (uma mensagem JSON por linha).
 *
 * Mensagem de request:  { "id": 1, "method": "transcribe", "params": {...} }
 * Mensagem de response: { "id": 1, "result": {...} }
 * Mensagem de evento:   { "event": "status_change", "data": {...} }
 */

import { appState, type AppStatus } from "./store.svelte";

type MessageHandler = (data: unknown) => void;

class SidecarBridge {
  private handlers = new Map<string, MessageHandler[]>();
  private nextId = 1;
  private pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

  async init() {
    // In dev mode, we'll use a WebSocket to communicate with the Python sidecar
    // In production, Tauri's shell plugin spawns the sidecar and we use stdin/stdout
    console.log("[sidecar] Initializing bridge...");
    appState.sidecarConnected = false;
    appState.status = "loading";
    appState.statusText = "Conectando ao backend...";

    // TODO: Fase 2 — conectar ao sidecar real
    // Por enquanto, simula conexao para desenvolvimento da UI
    setTimeout(() => {
      appState.sidecarConnected = true;
      appState.status = "idle";
      appState.statusText = "Pronto";
      console.log("[sidecar] Mock connection established");
    }, 1500);
  }

  destroy() {
    appState.sidecarConnected = false;
    this.handlers.clear();
    this.pending.clear();
  }

  send(method: string, params: Record<string, unknown> = {}): Promise<unknown> {
    const id = this.nextId++;
    const msg = { id, method, params };
    console.log("[sidecar] ->", msg);

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });

      // TODO: Fase 2 — enviar via Tauri shell plugin
      // Por enquanto, resolve imediatamente para dev
      setTimeout(() => {
        this.pending.delete(id);
        resolve({ ok: true });
      }, 100);
    });
  }

  on(event: string, handler: MessageHandler) {
    const list = this.handlers.get(event) ?? [];
    list.push(handler);
    this.handlers.set(event, list);
  }

  /** Processa mensagem recebida do sidecar */
  handleMessage(raw: string) {
    try {
      const msg = JSON.parse(raw);

      // Response to a request
      if ("id" in msg && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id)!;
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error));
        else resolve(msg.result);
        return;
      }

      // Event from sidecar
      if ("event" in msg) {
        const handlers = this.handlers.get(msg.event) ?? [];
        for (const h of handlers) h(msg.data);

        // Handle built-in events
        if (msg.event === "status_change") {
          appState.status = msg.data.status as AppStatus;
          appState.statusText = msg.data.text ?? "";
        } else if (msg.event === "realtime_text") {
          appState.realtimeText = msg.data.text ?? "";
        } else if (msg.event === "transcription_done") {
          appState.lastTranscription = msg.data.text ?? "";
        }
      }
    } catch (e) {
      console.error("[sidecar] Failed to parse message:", raw, e);
    }
  }
}

export const sidecar = new SidecarBridge();
