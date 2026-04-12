<script lang="ts">
  import { appState } from "./store.svelte";

  const statusColors: Record<string, string> = {
    idle: "bg-emerald-500",
    loading: "bg-amber-500 animate-pulse",
    recording: "bg-red-500 animate-pulse",
    transcribing: "bg-amber-500",
    done: "bg-blue-500",
    error: "bg-red-500",
  };

  const statusLabels: Record<string, string> = {
    idle: "Pronto",
    loading: "Carregando...",
    recording: "Gravando",
    transcribing: "Transcrevendo...",
    done: "Concluido",
    error: "Erro",
  };
</script>

<div class="flex items-center gap-2">
  <div class="flex items-center gap-1.5">
    <div
      class="w-2 h-2 rounded-full {statusColors[appState.status]}"
    ></div>
    <span class="text-xs text-[var(--text-muted)]">
      {appState.statusText || statusLabels[appState.status]}
    </span>
  </div>

  {#if !appState.sidecarConnected}
    <span class="text-xs text-red-400">Desconectado</span>
  {/if}
</div>
