<script lang="ts">
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import { invoke } from "@tauri-apps/api/core";
  import { appState, type Backend, type OutputMode } from "./store.svelte";
  import { sidecar } from "./sidecar";
  import Button from "./components/Button.svelte";
  import Input from "./components/Input.svelte";
  import HotkeyCapture from "./components/HotkeyCapture.svelte";

  type TabId = "geral" | "atalhos" | "prompt" | "api";

  let activeTab = $state<TabId>("geral");
  let saving = $state(false);
  let customPrompt = $state("");
  let apiKeys = $state<Record<string, string>>({
    openai: "",
    groq: "",
    gemini: "",
    deepgram: "",
  });

  // API key validation status per provider
  type KeyStatus = "idle" | "testing" | "ok" | "error";
  let apiKeyStatus = $state<Record<string, KeyStatus>>({
    openai: "idle",
    groq: "idle",
    gemini: "idle",
    deepgram: "idle",
  });
  let apiKeyMessages = $state<Record<string, string>>({});
  let debounceTimers: Record<string, ReturnType<typeof setTimeout>> = {};

  // Hotkey state — capturingHotkey coordena qual instancia esta capturando
  let hotkeys = $state({
    push_to_talk: "Ctrl+Alt+H",
    toggle: "Ctrl+Alt+T",
    cancel: "Ctrl+Alt+C",
    quit: "Ctrl+Q",
  });
  let capturingHotkey = $state<string | null>(null);

  // Load config on mount
  onMount(() => {
    sidecar.getConfig().then((config) => {
      if (config.custom_prompt) customPrompt = config.custom_prompt as string;
      if (config.api_keys) apiKeys = { ...apiKeys, ...(config.api_keys as Record<string, string>) };
      if (config.hotkeys) {
        const saved = config.hotkeys as Record<string, string>;
        for (const [k, v] of Object.entries(saved)) {
          if (k in hotkeys) (hotkeys as Record<string, string>)[k] = v;
        }
      }
    }).catch(() => {});
  });

  // Debounced API key validation — "testing" seta so apos debounce disparar
  function onApiKeyInput(provider: string, key: string) {
    clearTimeout(debounceTimers[provider]);
    if (!key || key.length < 8) {
      apiKeyStatus[provider] = "idle";
      apiKeyMessages[provider] = "";
      return;
    }
    debounceTimers[provider] = setTimeout(async () => {
      apiKeyStatus[provider] = "testing";
      try {
        const result = await sidecar.testApiKey(provider, key);
        if (result.ok) {
          apiKeyStatus[provider] = "ok";
          apiKeyMessages[provider] = result.latency_ms ? `${result.latency_ms}ms` : "";
        } else {
          apiKeyStatus[provider] = "error";
          apiKeyMessages[provider] = result.error ?? "Chave invalida";
        }
      } catch {
        apiKeyStatus[provider] = "idle";
      }
    }, 800);
  }

  const tabs: { id: TabId; label: string }[] = [
    { id: "geral", label: "Geral" },
    { id: "atalhos", label: "Atalhos" },
    { id: "prompt", label: "Prompt" },
    { id: "api", label: "API" },
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

  const hotkeyDefs: { id: keyof typeof hotkeys; label: string }[] = [
    { id: "push_to_talk", label: "Push-to-Talk" },
    { id: "toggle", label: "Gravar / Parar" },
    { id: "cancel", label: "Cancelar gravacao" },
    { id: "quit", label: "Sair do app" },
  ];

  async function handleSave() {
    saving = true;
    try {
      await sidecar.saveConfig({
        backend: appState.backend,
        output_mode: appState.outputMode,
        model: appState.model,
        realtime: appState.realtimeEnabled,
        custom_prompt: customPrompt,
        api_keys: apiKeys,
        hotkeys: { ...hotkeys },
        theme: appState.theme,
      });

      // Re-register global shortcuts with new hotkeys
      try {
        await invoke("update_shortcuts", {
          ptt: hotkeys.push_to_talk,
          toggle: hotkeys.toggle,
          cancel: hotkeys.cancel,
          quit: hotkeys.quit,
        });
      } catch {
        // update_shortcuts may not be available yet — non-fatal
      }

      sidecar.updateTrayInfo(appState.backend, appState.model);
    } finally {
      saving = false;
    }
  }
</script>

<div class="flex flex-col h-full p-4 gap-4">
  <!-- Tab bar -->
  <div class="flex gap-1 bg-[var(--bg-secondary)] rounded-[var(--radius-md)] p-1 shrink-0">
    {#each tabs as tab}
      <button
        class="flex-1 py-1.5 px-3 text-sm font-medium rounded-[var(--radius-sm)] transition-all duration-[120ms]
          {activeTab === tab.id
            ? 'bg-[var(--accent-blue)] text-white shadow-[var(--shadow-sm)]'
            : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'}"
        onclick={() => (activeTab = tab.id)}
      >
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Tab content (with fade transition) -->
  <div class="flex-1 overflow-y-auto min-h-0">
    {#if activeTab === "geral"}
      <div transition:fade={{ duration: 120 }} class="space-y-6">
        <!-- Output mode -->
        <fieldset class="space-y-2.5">
          <legend class="text-sm font-semibold text-[var(--text-primary)] mb-1">Modo de saida</legend>
          {#each [{ v: "cursor", l: "Colar no cursor (simula digitacao)" }, { v: "clipboard", l: "So clipboard (Ctrl+V manual)" }] as opt}
            <label class="flex items-center gap-3 cursor-pointer group">
              <input
                type="radio"
                name="output"
                value={opt.v}
                checked={appState.outputMode === opt.v}
                onchange={() => (appState.outputMode = opt.v as OutputMode)}
                class="accent-[var(--accent-blue)]"
              />
              <span class="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                {opt.l}
              </span>
            </label>
          {/each}
        </fieldset>

        <hr class="border-[var(--border)]" />

        <!-- Model -->
        <fieldset class="space-y-2.5">
          <legend class="text-sm font-semibold text-[var(--text-primary)] mb-1">Modelo Whisper (backend local)</legend>
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
              <span class="text-sm text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                {m.label}
              </span>
            </label>
          {/each}
        </fieldset>
      </div>

    {:else if activeTab === "atalhos"}
      <div transition:fade={{ duration: 120 }} class="space-y-4">
        <p class="text-sm text-[var(--text-muted)]">
          Clique no botao e pressione a nova combinacao. Salve para aplicar.
        </p>
        {#each hotkeyDefs as def}
          <HotkeyCapture
            bind:value={hotkeys[def.id]}
            label={def.label}
            captureId={def.id}
            activeCaptureId={capturingHotkey}
            onCaptureStart={(id) => (capturingHotkey = id)}
            onCaptureEnd={() => (capturingHotkey = null)}
          />
        {/each}
        <p class="text-xs text-[var(--text-muted)] mt-2">
          Atalhos globais funcionam mesmo com o app minimizado.
        </p>
      </div>

    {:else if activeTab === "prompt"}
      <div transition:fade={{ duration: 120 }} class="space-y-4">
        <label class="block">
          <span class="text-sm font-semibold text-[var(--text-primary)]">
            Prompt personalizado
          </span>
          <textarea
            bind:value={customPrompt}
            placeholder="Cole aqui um texto de exemplo no estilo que voce quer que a transcricao siga..."
            class="mt-2 w-full h-44 px-4 py-3 text-sm bg-[var(--bg-secondary)] border border-[var(--border)]
              rounded-[var(--radius-md)] text-[var(--text-secondary)] placeholder:text-[var(--text-muted)]
              focus:outline-none focus:border-[var(--accent-blue)] focus:ring-1 focus:ring-[var(--accent-blue)]/30
              resize-none transition-colors"
          ></textarea>
        </label>
      </div>

    {:else if activeTab === "api"}
      <div transition:fade={{ duration: 120 }} class="space-y-5">
        <!-- Backend selector -->
        <div class="space-y-1.5">
          <span class="text-sm font-semibold text-[var(--text-primary)]">Backend</span>
          <select
            bind:value={appState.backend}
            class="w-full px-3 py-2 text-sm bg-[var(--bg-secondary)] border border-[var(--border)]
              rounded-[var(--radius-md)] text-[var(--text-secondary)] focus:outline-none
              focus:border-[var(--accent-blue)] transition-colors"
          >
            {#each backendOptions as opt}
              <option value={opt.value}>{opt.label}</option>
            {/each}
          </select>
        </div>

        <!-- API Keys with inline validation -->
        {#if appState.backend !== "local"}
          <div class="space-y-3">
            <span class="text-sm font-semibold text-[var(--text-primary)]">API Keys</span>
            {#each ["openai", "groq", "gemini", "deepgram"] as provider}
              <div class="space-y-1">
                <span class="text-xs text-[var(--text-muted)] capitalize">{provider}</span>
                <Input
                  bind:value={apiKeys[provider]}
                  type="password"
                  placeholder="sk-..."
                  mono={true}
                  status={apiKeyStatus[provider]}
                  statusMessage={apiKeyMessages[provider]}
                  oninput={(e) => onApiKeyInput(provider, (e.target as HTMLInputElement).value)}
                />
              </div>
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
  <div class="shrink-0">
    <Button variant="primary" loading={saving} onclick={handleSave}>
      Salvar
    </Button>
  </div>
</div>
