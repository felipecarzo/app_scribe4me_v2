<script lang="ts">
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import { invoke } from "@tauri-apps/api/core";
  import { appState, type Backend, type OutputMode } from "./store.svelte";
  import { sidecar } from "./sidecar";
  import Button from "./components/Button.svelte";
  import Input from "./components/Input.svelte";
  import HotkeyCapture from "./components/HotkeyCapture.svelte";

  type TabId = "geral" | "atalhos" | "prompt" | "api" | "profiles";

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

  // --- Profiles state ---
  type ProfileEntry = { name: string; prompt: string; code_mode: boolean; builtin: boolean };
  let profiles = $state<ProfileEntry[]>([]);
  let editingProfile = $state<ProfileEntry | null>(null);
  let isNewProfile = $state(false);
  let profileSaving = $state(false);
  let profileDeleteConfirm = $state<string | null>(null);

  async function loadProfiles() {
    profiles = await sidecar.listProfiles();
  }

  async function selectProfile(name: string) {
    await sidecar.setActiveProfile(name);
    appState.activeProfile = name;
    const p = profiles.find((x) => x.name === name);
    if (p) appState.codeMode = p.code_mode;
  }

  function startNewProfile() {
    editingProfile = { name: "", prompt: "", code_mode: false, builtin: false };
    isNewProfile = true;
  }

  function startEditProfile(p: ProfileEntry) {
    editingProfile = { ...p };
    isNewProfile = false;
  }

  async function saveEditingProfile() {
    if (!editingProfile || !editingProfile.name.trim() || !editingProfile.prompt.trim()) return;
    profileSaving = true;
    try {
      await sidecar.saveProfile(editingProfile.name.trim(), editingProfile.prompt.trim(), editingProfile.code_mode);
      await loadProfiles();
      editingProfile = null;
    } finally {
      profileSaving = false;
    }
  }

  async function deleteProfile(name: string) {
    await sidecar.deleteProfile(name);
    profileDeleteConfirm = null;
    await loadProfiles();
    if (appState.activeProfile === name) {
      await selectProfile("Tech-Dev");
    }
  }

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
    loadProfiles();
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
    { id: "profiles", label: "Profiles" },
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

    {:else if activeTab === "profiles"}
      <div transition:fade={{ duration: 120 }} class="space-y-4">
        {#if editingProfile}
          <!-- Editor de profile -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm font-semibold text-[var(--text-primary)]">
                {isNewProfile ? "Novo Profile" : "Editar Profile"}
              </span>
              <button
                onclick={() => (editingProfile = null)}
                class="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
              >
                Cancelar
              </button>
            </div>

            <div class="space-y-1">
              <label class="text-xs text-[var(--text-muted)]">Nome</label>
              <input
                bind:value={editingProfile.name}
                disabled={!isNewProfile && editingProfile.builtin}
                placeholder="Tech-Dev"
                class="w-full px-3 py-2 text-sm bg-[var(--bg-secondary)] border border-[var(--border)]
                  rounded-[var(--radius-md)] text-[var(--text-secondary)] focus:outline-none
                  focus:border-[var(--accent-blue)] disabled:opacity-50 transition-colors"
              />
            </div>

            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                bind:checked={editingProfile.code_mode}
                class="accent-[var(--accent-blue)] w-4 h-4"
              />
              <span class="text-sm text-[var(--text-secondary)]">Code Mode (Voice Coding)</span>
            </label>

            <div class="space-y-1">
              <label class="text-xs text-[var(--text-muted)]">Prompt (initial_prompt para o Whisper)</label>
              <textarea
                bind:value={editingProfile.prompt}
                placeholder="Texto de exemplo no estilo e vocabulario do seu dominio..."
                class="w-full h-32 px-3 py-2 text-sm bg-[var(--bg-secondary)] border border-[var(--border)]
                  rounded-[var(--radius-md)] text-[var(--text-secondary)] placeholder:text-[var(--text-muted)]
                  focus:outline-none focus:border-[var(--accent-blue)] resize-none transition-colors"
              ></textarea>
            </div>

            <Button variant="primary" loading={profileSaving} onclick={saveEditingProfile}>
              Salvar profile
            </Button>
          </div>
        {:else}
          <!-- Lista de profiles -->
          <p class="text-xs text-[var(--text-muted)]">
            Profiles definem o <em>initial_prompt</em> do Whisper para melhorar reconhecimento por dominio.
          </p>

          <div class="space-y-2">
            {#each profiles as p}
              <div
                class="flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] border transition-all
                  {appState.activeProfile === p.name
                    ? 'border-[var(--accent-blue)] bg-[var(--accent-blue)]/10'
                    : 'border-[var(--border)] bg-[var(--bg-secondary)] hover:border-[var(--border-hover)]'}"
              >
                <button
                  class="flex-1 text-left min-w-0"
                  onclick={() => selectProfile(p.name)}
                >
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-[var(--text-primary)] truncate">{p.name}</span>
                    {#if p.code_mode}
                      <span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[var(--accent-blue)]/20 text-[var(--accent-blue)] shrink-0">
                        CODE
                      </span>
                    {/if}
                    {#if p.builtin}
                      <span class="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)] shrink-0">
                        builtin
                      </span>
                    {/if}
                  </div>
                </button>

                <button
                  onclick={() => startEditProfile(p)}
                  class="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors shrink-0"
                >
                  Editar
                </button>

                {#if !p.builtin}
                  {#if profileDeleteConfirm === p.name}
                    <button
                      onclick={() => deleteProfile(p.name)}
                      class="text-xs text-red-400 hover:text-red-300 transition-colors shrink-0"
                    >
                      Confirmar
                    </button>
                    <button
                      onclick={() => (profileDeleteConfirm = null)}
                      class="text-xs text-[var(--text-muted)] transition-colors shrink-0"
                    >
                      Cancelar
                    </button>
                  {:else}
                    <button
                      onclick={() => (profileDeleteConfirm = p.name)}
                      class="text-xs text-[var(--text-muted)] hover:text-red-400 transition-colors shrink-0"
                    >
                      Deletar
                    </button>
                  {/if}
                {/if}
              </div>
            {/each}
          </div>

          <Button variant="ghost" onclick={startNewProfile}>
            + Novo profile
          </Button>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Save button — oculto na aba profiles (salva inline) -->
  <div class="shrink-0">
    {#if activeTab !== "profiles"}
      <Button variant="primary" loading={saving} onclick={handleSave}>
        Salvar
      </Button>
    {/if}
  </div>
</div>
