<script lang="ts">
  import { onMount } from "svelte";
  import { appState, type Backend, type OutputMode } from "./store.svelte";
  import { sidecar } from "./sidecar";

  let activeTab = $state<"geral" | "prompt" | "api">("geral");
  let customPrompt = $state("");
  let apiKeys = $state<Record<string, string>>({
    openai: "",
    groq: "",
    gemini: "",
    deepgram: "",
  });

  // Load config from sidecar on mount (onMount avoids $effect dependency loops)
  onMount(() => {
    sidecar.getConfig().then((config) => {
      if (config.custom_prompt) customPrompt = config.custom_prompt as string;
      if (config.api_keys) apiKeys = { ...apiKeys, ...(config.api_keys as Record<string, string>) };
    }).catch(() => {});
  });

  const tabs = [
    { id: "geral" as const, label: "Geral" },
    { id: "prompt" as const, label: "Prompt" },
    { id: "api" as const, label: "API" },
  ];

  const backendOptions: { value: Backend; label: string }[] = [
    { value: "local", label: "Local (Whisper — offline)" },
    { value: "openai", label: "OpenAI (whisper-1)" },
    { value: "groq", label: "Groq (whisper-large-v3)" },
    { value: "gemini", label: "Gemini Flash (Google)" },
    { value: "deepgram", label: "Deepgram Nova-2" },
  ];

  const models = [
    { value: "tiny", label: "Tiny (75MB) — rapido, baixa precisao" },
    { value: "base", label: "Base (142MB) — equilibrado" },
    { value: "small", label: "Small (466MB) — bom para PT-BR" },
    { value: "medium", label: "Medium (1.5GB) — muito bom" },
    { value: "large-v3", label: "Large-v3 (3GB) — maximo de qualidade" },
  ];

  async function handleSave() {
    await sidecar.saveConfig({
      backend: appState.backend,
      output_mode: appState.outputMode,
      model: appState.model,
      realtime: appState.realtimeEnabled,
      custom_prompt: customPrompt,
      api_keys: apiKeys,
    });
    // Update tray menu labels
    sidecar.updateTrayInfo(appState.backend, appState.model);
  }
</script>

<div class="flex flex-col h-full p-4 gap-4">
  <!-- Tab bar -->
  <div class="flex gap-1 bg-[var(--bg-secondary)] rounded-lg p-1">
    {#each tabs as tab}
      <button
        class="flex-1 py-2 px-3 text-sm font-medium rounded-md transition-all
          {activeTab === tab.id
            ? 'bg-[var(--accent-blue)] text-white shadow-sm'
            : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'}"
        onclick={() => (activeTab = tab.id)}
      >
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Tab content -->
  <div class="flex-1 overflow-y-auto">
    {#if activeTab === "geral"}
      <div class="space-y-6">
        <!-- Output mode -->
        <fieldset class="space-y-3">
          <legend class="text-sm font-semibold text-[var(--text-primary)]">Modo de saida</legend>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input
              type="radio"
              name="output"
              value="cursor"
              checked={appState.outputMode === "cursor"}
              onchange={() => (appState.outputMode = "cursor")}
              class="accent-[var(--accent-blue)]"
            />
            <span class="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
              Colar no cursor (simula digitacao)
            </span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input
              type="radio"
              name="output"
              value="clipboard"
              checked={appState.outputMode === "clipboard"}
              onchange={() => (appState.outputMode = "clipboard")}
              class="accent-[var(--accent-blue)]"
            />
            <span class="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
              So clipboard (Ctrl+V manual)
            </span>
          </label>
        </fieldset>

        <hr class="border-[var(--border)]" />

        <!-- Model -->
        <fieldset class="space-y-3">
          <legend class="text-sm font-semibold text-[var(--text-primary)]">Modelo Whisper (backend local)</legend>
          {#each models as m}
            <label class="flex items-center gap-3 cursor-pointer group">
              <input
                type="radio"
                name="model"
                value={m.value}
                checked={appState.model === m.value}
                onchange={() => (appState.model = m.value)}
                class="accent-[var(--accent-blue)]"
              />
              <span class="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                {m.label}
              </span>
            </label>
          {/each}
        </fieldset>
      </div>

    {:else if activeTab === "prompt"}
      <div class="space-y-4">
        <label class="block">
          <span class="text-sm font-semibold text-[var(--text-primary)]">
            Prompt personalizado
          </span>
          <textarea
            bind:value={customPrompt}
            placeholder="Cole aqui um texto de exemplo no estilo que voce quer que a transcricao siga..."
            class="mt-2 w-full h-48 px-4 py-3 text-sm bg-[var(--bg-secondary)] border border-[var(--border)]
              rounded-lg text-[var(--text-secondary)] placeholder:text-[var(--text-muted)]
              focus:outline-none focus:border-[var(--accent-blue)] focus:ring-1 focus:ring-[var(--accent-blue)]
              resize-none"
          ></textarea>
        </label>
      </div>

    {:else if activeTab === "api"}
      <div class="space-y-6">
        <!-- Backend selector -->
        <div class="space-y-2">
          <span class="text-sm font-semibold text-[var(--text-primary)]">Backend</span>
          <select
            bind:value={appState.backend}
            class="w-full px-3 py-2 text-sm bg-[var(--bg-secondary)] border border-[var(--border)]
              rounded-lg text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)]"
          >
            {#each backendOptions as opt}
              <option value={opt.value}>{opt.label}</option>
            {/each}
          </select>
        </div>

        <!-- API Keys -->
        {#if appState.backend !== "local"}
          <div class="space-y-3">
            <span class="text-sm font-semibold text-[var(--text-primary)]">API Keys</span>
            {#each ["openai", "groq", "gemini", "deepgram"] as provider}
              <label class="block space-y-1">
                <span class="text-xs text-[var(--text-muted)] capitalize">{provider}</span>
                <input
                  type="password"
                  bind:value={apiKeys[provider]}
                  placeholder="sk-..."
                  class="w-full px-3 py-2 text-sm font-mono bg-[var(--bg-secondary)] border border-[var(--border)]
                    rounded-lg text-[var(--text-secondary)] placeholder:text-[var(--text-muted)]
                    focus:outline-none focus:border-[var(--accent-blue)]"
                />
              </label>
            {/each}
          </div>
        {/if}

        <!-- Realtime toggle -->
        {#if appState.backend === "deepgram"}
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              bind:checked={appState.realtimeEnabled}
              class="accent-[var(--accent-blue)] w-4 h-4"
            />
            <span class="text-sm text-[var(--text-secondary)]">
              Tempo real (texto parcial ao falar)
            </span>
          </label>
        {/if}

        <p class="text-xs text-[var(--text-muted)]">
          Groq (gratis) | OpenAI ($0.006/min) | Gemini (free tier) | Deepgram (200h/mes gratis)
        </p>
      </div>
    {/if}
  </div>

  <!-- Save button -->
  <button
    onclick={handleSave}
    class="w-full py-2.5 text-sm font-semibold rounded-lg bg-[var(--accent-green)] text-white
      hover:bg-emerald-600 transition-colors active:scale-[0.98]"
  >
    Salvar
  </button>
</div>
