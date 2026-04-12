/**
 * Protocolo de comunicacao com o sidecar Python via JSON-RPC.
 *
 * O sidecar Python e lancado pelo Tauri como processo filho.
 * Requests: frontend -> Tauri command -> stdin do sidecar.
 * Responses: stdout do sidecar -> Tauri -> frontend.
 * Events: stdout do sidecar -> Tauri emit -> frontend listen.
 */

import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import {
  isPermissionGranted,
  requestPermission,
  sendNotification,
} from "@tauri-apps/plugin-notification";
import { appState, type AppStatus } from "./store.svelte";

type MessageHandler = (data: unknown) => void;

class SidecarBridge {
  private handlers = new Map<string, MessageHandler[]>();
  private unlisten: UnlistenFn | null = null;

  async init() {
    console.log("[sidecar] Initializing bridge...");
    appState.sidecarConnected = false;
    appState.status = "loading";
    appState.statusText = "Conectando ao backend...";

    // Listen for sidecar events forwarded by Tauri
    this.unlisten = await listen<{ event: string; data: Record<string, unknown> }>(
      "sidecar-event",
      (ev) => {
        this.handleEvent(ev.payload.event, ev.payload.data);
      }
    );

    // Ping the sidecar to verify connection, then load config
    try {
      await this.send("ping");
      appState.sidecarConnected = true;
      console.log("[sidecar] Connected");

      // Load real config from sidecar and sync appState
      const config = await this.getConfig();
      appState.backend = (config.backend as typeof appState.backend) ?? "local";
      appState.model = (config.model as string) ?? "large-v3";
      appState.outputMode = (config.output_mode as typeof appState.outputMode) ?? "cursor";
      appState.realtimeEnabled = (config.realtime as boolean) ?? false;

      // Update tray menu with real config
      this.updateTrayInfo(appState.backend, appState.model);
    } catch (e) {
      console.error("[sidecar] Failed to connect:", e);
      appState.status = "error";
      appState.statusText = "Backend nao disponivel";
    }
  }

  destroy() {
    if (this.unlisten) {
      this.unlisten();
      this.unlisten = null;
    }
    appState.sidecarConnected = false;
    this.handlers.clear();
  }

  /** Send a JSON-RPC request to the sidecar via Tauri command. */
  async send(method: string, params: Record<string, unknown> = {}): Promise<unknown> {
    console.log("[sidecar] ->", method, params);
    const result = await invoke("sidecar_send", { method, params });
    console.log("[sidecar] <-", method, result);
    return result;
  }

  /** Register a handler for a sidecar event. */
  on(event: string, handler: MessageHandler) {
    const list = this.handlers.get(event) ?? [];
    list.push(handler);
    this.handlers.set(event, list);
  }

  // --- Typed API methods ---

  async getConfig(): Promise<Record<string, unknown>> {
    return (await this.send("get_config")) as Record<string, unknown>;
  }

  async saveConfig(data: Record<string, unknown>): Promise<void> {
    await this.send("save_config", data);
  }

  async getHardware(): Promise<Record<string, unknown>> {
    return (await this.send("get_hardware")) as Record<string, unknown>;
  }

  async loadModel(model: string): Promise<void> {
    await this.send("load_model", { model });
  }

  async startRecording(): Promise<void> {
    await this.send("start_recording");
  }

  async stopRecording(): Promise<Record<string, unknown>> {
    return (await this.send("stop_recording")) as Record<string, unknown>;
  }

  async cancelRecording(): Promise<void> {
    await this.send("cancel_recording");
  }

  async copyToClipboard(text: string): Promise<void> {
    await this.send("copy_to_clipboard", { text });
  }

  /** Update tray menu labels for backend and model. */
  async updateTrayInfo(backend: string, model: string): Promise<void> {
    await invoke("update_tray_info", { backend, model });
  }

  // --- Internal event handling ---

  private handleEvent(eventName: string, data: Record<string, unknown>) {
    // Dispatch to registered handlers
    const handlers = this.handlers.get(eventName) ?? [];
    for (const h of handlers) h(data);

    // Handle built-in events
    if (eventName === "status_change") {
      const prevStatus = appState.status;
      appState.status = (data.status as AppStatus) ?? "idle";
      appState.statusText = (data.text as string) ?? "";

      // Native notifications for key transitions
      if (appState.status === "error") {
        this.notify("Erro", (data.text as string) ?? "Erro na transcricao");
      } else if (prevStatus === "transcribing" && appState.status === "idle") {
        this.notify("Transcricao concluida", "Texto copiado para o clipboard");
      }
    } else if (eventName === "realtime_text") {
      appState.realtimeText = (data.text as string) ?? "";
    } else if (eventName === "paste_ready") {
      appState.lastTranscription = (data.text as string) ?? "";
      this.notify("Texto pronto", "Colado na posicao do cursor");
    }
  }

  /** Send a native OS notification. */
  private async notify(title: string, body: string) {
    try {
      let granted = await isPermissionGranted();
      if (!granted) {
        const permission = await requestPermission();
        granted = permission === "granted";
      }
      if (granted) {
        sendNotification({ title, body });
      }
    } catch {
      // Notifications not available (e.g., dev mode without plugin)
    }
  }
}

export const sidecar = new SidecarBridge();
