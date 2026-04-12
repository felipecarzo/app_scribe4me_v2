<script lang="ts">
  import "./app.css";
  import Settings from "./lib/Settings.svelte";
  import StatusBar from "./lib/StatusBar.svelte";
  import Onboarding from "./lib/components/Onboarding.svelte";
  import ThemeToggle from "./lib/components/ThemeToggle.svelte";
  import { sidecar } from "./lib/sidecar";
  import { appState } from "./lib/store.svelte";

  // Initialize sidecar connection on mount
  $effect(() => {
    sidecar.init();
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
