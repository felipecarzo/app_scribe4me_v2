<script lang="ts">
  import { fly } from "svelte/transition";
  import { sidecar } from "../sidecar";
  import { appState } from "../store.svelte";
  import Button from "./Button.svelte";

  let step = $state(0);
  let finishing = $state(false);
  let hardware = $state<Record<string, unknown> | null>(null);
  let hardwareLoading = $state(false);

  const totalSteps = 3;

  // Load hardware info when step 2 is shown
  $effect(() => {
    if (step === 1 && hardware === null && appState.sidecarConnected) {
      hardwareLoading = true;
      sidecar.getHardware().then((hw) => {
        hardware = hw;
      }).catch(() => {
        hardware = {};
      }).finally(() => {
        hardwareLoading = false;
      });
    }
  });

  function next() {
    if (step < totalSteps - 1) step++;
  }

  function prev() {
    if (step > 0) step--;
  }

  async function finish() {
    finishing = true;
    try {
      await sidecar.saveConfig({
        backend: appState.backend,
        output_mode: appState.outputMode,
        model: appState.model,
        realtime: false,
        first_run: false,
        theme: appState.theme,
      });
      appState.firstRun = false;
    } finally {
      finishing = false;
    }
  }

  function acceptHardwareSuggestion() {
    const suggested = hardware?.recommended_model as string | undefined;
    if (suggested) appState.model = suggested;
    next();
  }
</script>

<div class="flex flex-col h-full p-6 gap-6">
  <!-- Progress dots -->
  <div class="flex items-center justify-center gap-2">
    {#each Array(totalSteps) as _, i}
      <div
        class="rounded-full transition-all duration-[220ms]
          {i === step ? 'w-4 h-2 bg-[var(--accent-blue)]' : 'w-2 h-2 bg-[var(--bg-tertiary)]'}"
      ></div>
    {/each}
  </div>

  <!-- Step content -->
  <div class="flex-1 flex flex-col justify-center">
    {#if step === 0}
      <div transition:fly={{ x: -20, duration: 200 }} class="space-y-4 text-center">
        <div class="text-4xl">🎙</div>
        <h1 class="text-xl font-bold text-[var(--text-primary)]">Bem-vindo ao Scribe4me</h1>
        <p class="text-sm text-[var(--text-secondary)] leading-relaxed">
          Transforme fala em texto com IA — offline ou via API.
          Pressione um atalho, fale, e o texto aparece onde voce estiver.
        </p>
        <div class="bg-[var(--bg-secondary)] rounded-[var(--radius-md)] p-4 text-left space-y-2">
          <p class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">Atalho principal</p>
          <p class="text-sm text-[var(--text-primary)] font-mono">Ctrl + Alt + T — Gravar / Parar</p>
          <p class="text-sm text-[var(--text-primary)] font-mono">Ctrl + Alt + H — Push-to-Talk</p>
        </div>
      </div>

    {:else if step === 1}
      <div transition:fly={{ x: -20, duration: 200 }} class="space-y-4">
        <h2 class="text-lg font-bold text-[var(--text-primary)]">Hardware detectado</h2>

        {#if hardwareLoading}
          <div class="flex items-center gap-3 text-[var(--text-muted)]">
            <svg class="animate-spin-sm w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span class="text-sm">Detectando hardware...</span>
          </div>
        {:else if hardware}
          <div class="bg-[var(--bg-secondary)] rounded-[var(--radius-md)] p-4 space-y-2">
            {#if hardware.gpu_name}
              <div class="flex justify-between text-sm">
                <span class="text-[var(--text-muted)]">GPU</span>
                <span class="text-[var(--text-primary)]">{hardware.gpu_name}</span>
              </div>
            {/if}
            {#if hardware.ram_gb}
              <div class="flex justify-between text-sm">
                <span class="text-[var(--text-muted)]">RAM</span>
                <span class="text-[var(--text-primary)]">{hardware.ram_gb} GB</span>
              </div>
            {/if}
            <div class="flex justify-between text-sm">
              <span class="text-[var(--text-muted)]">Modelo recomendado</span>
              <span class="text-[var(--accent-green)] font-semibold">{hardware.recommended_model ?? "large-v3"}</span>
            </div>
          </div>
          <p class="text-xs text-[var(--text-muted)]">
            Voce pode alterar o modelo depois em Configuracoes.
          </p>
        {:else}
          <p class="text-sm text-[var(--text-muted)]">
            Hardware nao disponivel. O modelo large-v3 sera usado.
          </p>
        {/if}
      </div>

    {:else if step === 2}
      <div transition:fly={{ x: -20, duration: 200 }} class="space-y-4">
        <h2 class="text-lg font-bold text-[var(--text-primary)]">Como inserir o texto?</h2>
        <p class="text-sm text-[var(--text-secondary)]">
          Escolha como o texto transcrito chega ate voce.
        </p>

        {#each [
          { v: "cursor", l: "Colar no cursor", d: "Digita automaticamente onde o cursor estiver" },
          { v: "clipboard", l: "Apenas clipboard", d: "Copia para Ctrl+V manual" }
        ] as opt}
          <button
            class="w-full text-left p-4 rounded-[var(--radius-md)] border transition-all duration-[120ms]
              {appState.outputMode === opt.v
                ? 'border-[var(--accent-blue)] bg-[var(--accent-blue)]/10'
                : 'border-[var(--border)] bg-[var(--bg-secondary)] hover:border-[var(--accent-blue)]/50'}"
            onclick={() => (appState.outputMode = opt.v as "cursor" | "clipboard")}
          >
            <p class="text-sm font-semibold text-[var(--text-primary)]">{opt.l}</p>
            <p class="text-xs text-[var(--text-muted)] mt-0.5">{opt.d}</p>
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Navigation buttons -->
  <div class="flex gap-3 shrink-0">
    {#if step > 0}
      <Button variant="ghost" onclick={prev}>Anterior</Button>
    {/if}

    {#if step < totalSteps - 1}
      <Button variant="primary" onclick={step === 1 && hardware ? acceptHardwareSuggestion : next}>
        {step === 1 && hardware ? "Aceitar sugestao" : "Proximo"}
      </Button>
      {#if step === 1 && hardware}
        <Button variant="ghost" onclick={next}>Escolher manualmente</Button>
      {/if}
    {:else}
      <Button variant="primary" loading={finishing} onclick={finish}>
        Comecar a usar
      </Button>
    {/if}
  </div>
</div>
