<script lang="ts">
  import { appState, type Theme } from "../store.svelte";

  const options: { value: Theme; title: string; icon: string }[] = [
    { value: "light", title: "Tema claro", icon: "☀" },
    { value: "dark",  title: "Tema escuro", icon: "🌙" },
    { value: "system", title: "Seguir sistema", icon: "⊙" },
  ];
</script>

<div class="flex items-center gap-0.5 bg-[var(--bg-tertiary)] rounded-[var(--radius-sm)] p-0.5">
  {#each options as opt}
    <button
      title={opt.title}
      onclick={() => (appState.theme = opt.value)}
      class="w-6 h-6 flex items-center justify-center text-xs rounded-[4px] transition-all duration-[120ms]
        {appState.theme === opt.value
          ? 'bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-[var(--shadow-sm)]'
          : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'}"
    >
      {opt.icon}
    </button>
  {/each}
</div>
