<script lang="ts">
  interface Props {
    value?: string;
    type?: "text" | "password" | "email";
    placeholder?: string;
    status?: "idle" | "testing" | "ok" | "error";
    statusMessage?: string;
    mono?: boolean;
    onchange?: (e: Event) => void;
    oninput?: (e: Event) => void;
  }

  let {
    value = $bindable(""),
    type = "text",
    placeholder = "",
    status = "idle",
    statusMessage = "",
    mono = false,
    onchange,
    oninput,
  }: Props = $props();
</script>

<div class="relative">
  <input
    bind:value
    {type}
    {placeholder}
    {onchange}
    {oninput}
    class="w-full px-3 py-2 pr-9 text-sm bg-[var(--bg-secondary)] border rounded-[var(--radius-md)]
      text-[var(--text-secondary)] placeholder:text-[var(--text-muted)]
      focus:outline-none focus:ring-1 transition-colors duration-[120ms]
      {mono ? 'font-mono' : ''}
      {status === 'error'
        ? 'border-[var(--accent-red)] focus:border-[var(--accent-red)] focus:ring-[var(--accent-red)]/30'
        : status === 'ok'
        ? 'border-[var(--accent-green)] focus:border-[var(--accent-green)] focus:ring-[var(--accent-green)]/30'
        : 'border-[var(--border)] focus:border-[var(--accent-blue)] focus:ring-[var(--accent-blue)]/30'}"
  />

  <!-- Status adornment -->
  {#if status !== "idle"}
    <div
      class="absolute right-2.5 top-1/2 -translate-y-1/2"
      title={statusMessage}
    >
      {#if status === "testing"}
        <svg class="animate-spin-sm w-4 h-4 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      {:else if status === "ok"}
        <svg class="w-4 h-4 text-[var(--accent-green)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      {:else if status === "error"}
        <svg class="w-4 h-4 text-[var(--accent-red)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      {/if}
    </div>
  {/if}
</div>

{#if status === "error" && statusMessage}
  <p class="mt-1 text-xs text-[var(--accent-red)]">{statusMessage}</p>
{/if}
