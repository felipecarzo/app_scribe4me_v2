<script lang="ts">
  import "./app.css";
  import Settings from "./lib/Settings.svelte";
  import StatusBar from "./lib/StatusBar.svelte";
  import { sidecar } from "./lib/sidecar";
  import { appState } from "./lib/store.svelte";

  // Initialize sidecar connection on mount
  $effect(() => {
    sidecar.init();
    return () => sidecar.destroy();
  });
</script>

<main class="flex flex-col h-screen bg-[var(--bg-primary)]">
  <div
    data-tauri-drag-region
    class="h-8 flex items-center justify-between px-4 bg-[var(--bg-secondary)] border-b border-[var(--border)]"
  >
    <span class="text-xs font-semibold text-[var(--text-muted)]">Scribe4me</span>
    <StatusBar />
  </div>

  <div class="flex-1 overflow-y-auto">
    <Settings />
  </div>
</main>
