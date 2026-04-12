/**
 * Estado global reativo do Scribe4me usando Svelte 5 runes.
 *
 * Estados do app:
 * - idle: pronto para gravar (verde)
 * - loading: carregando modelo Whisper (amarelo pulsante)
 * - recording: gravando audio (vermelho)
 * - transcribing: processando transcricao (amarelo)
 * - done: transcricao concluida, copiada (azul)
 * - error: erro na operacao (vermelho)
 */

export type AppStatus =
  | "idle"
  | "loading"
  | "recording"
  | "transcribing"
  | "done"
  | "error";

export type Backend = "local" | "openai" | "groq" | "gemini" | "deepgram";
export type OutputMode = "cursor" | "clipboard";

interface AppState {
  status: AppStatus;
  statusText: string;
  backend: Backend;
  outputMode: OutputMode;
  model: string;
  realtimeEnabled: boolean;
  realtimeText: string;
  lastTranscription: string;
  sidecarConnected: boolean;
}

export const appState: AppState = $state({
  status: "loading",
  statusText: "Iniciando...",
  backend: "local",
  outputMode: "cursor",
  model: "large-v3",
  realtimeEnabled: false,
  realtimeText: "",
  lastTranscription: "",
  sidecarConnected: false,
});
