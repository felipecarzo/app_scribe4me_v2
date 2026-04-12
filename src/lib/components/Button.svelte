<script lang="ts">
  interface Props {
    variant?: "primary" | "ghost" | "danger";
    loading?: boolean;
    disabled?: boolean;
    type?: "button" | "submit";
    onclick?: (e: MouseEvent) => void;
    children: import("svelte").Snippet;
  }

  let {
    variant = "primary",
    loading = false,
    disabled = false,
    type = "button",
    onclick,
    children,
  }: Props = $props();

  const variantClasses: Record<string, string> = {
    primary: "bg-[var(--accent-green)] text-white hover:brightness-110",
    ghost: "bg-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] border border-[var(--border)]",
    danger: "bg-[var(--accent-red)] text-white hover:brightness-110",
  };
</script>

<button
  {type}
  {onclick}
  disabled={disabled || loading}
  class="relative flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold
    rounded-[var(--radius-md)] transition-all duration-[120ms]
    active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed
    {variantClasses[variant]}"
>
  {#if loading}
    <svg
      class="animate-spin-sm w-4 h-4 shrink-0"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  {/if}
  {@render children()}
</button>
