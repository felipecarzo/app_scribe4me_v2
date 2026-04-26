<script lang="ts">
  import "./app.css";
  import { invoke } from "@tauri-apps/api/core";
  import Settings from "./lib/Settings.svelte";
  import StatusBar from "./lib/StatusBar.svelte";
  import Onboarding from "./lib/components/Onboarding.svelte";
  import ThemeToggle from "./lib/components/ThemeToggle.svelte";
  import { sidecar } from "./lib/sidecar";
  import { appState } from "./lib/store.svelte";

  async function hideWindow() {
    try {
      await invoke("hide_main_window");
    } catch (e) {
      console.error("[App] hide_main_window failed:", e);
    }
  }
  // Expor pra Settings chamar apos salvar
  (window as any).__hideMainWindow = hideWindow;

  // Initialize sidecar connection on mount — catch async errors
  let initialized = $state(false);
  $effect(() => {
    if (initialized) return;
    initialized = true;
    sidecar.init().catch((e) => {
      console.error("[App] Sidecar init crashed:", e);
      appState.status = "error";
      appState.statusText = `Init crashed: ${String(e)}`;
    });
    return () => sidecar.destroy();
  });

  // Apply theme to <html> whenever appState.theme changes
  $effect(() => {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const resolved =
      appState.theme === "system"
        ? prefersDark ? "dark" : "light"
        : appState.theme;
    document.documentElement.setAttribute("data-theme", resolved);
    // Cache for anti-FOWT script on next load
    try { localStorage.setItem("scribe-theme", JSON.stringify({ theme: appState.theme })); } catch {}
  });
</script>

<main class="flex flex-col h-screen bg-[var(--bg-primary)] transition-colors duration-[220ms]">
  <!-- Title bar / drag region -->
  <div
    data-tauri-drag-region
    class="h-9 flex items-center justify-between px-4 bg-[var(--bg-secondary)]
      border-b border-[var(--border)] shrink-0"
  >
    <span class="text-xs font-semibold text-[var(--text-muted)] select-none">Scribe4me</span>
    <div class="flex items-center gap-3">
      <StatusBar />
      <ThemeToggle />
      <button
        onclick={hideWindow}
        class="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-lg leading-none px-1"
        title="Fechar (esconde no tray)"
        aria-label="Fechar"
      >
        ×
      </button>
    </div>
  </div>

  <!-- Main content -->
  <div class="flex-1 overflow-y-auto">
    {#if appState.firstRun}
      <Onboarding />
    {:else}
      <Settings />
    {/if}
  </div>
</main>
