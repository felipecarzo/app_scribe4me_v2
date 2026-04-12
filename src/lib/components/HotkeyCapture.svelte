<script lang="ts">
  interface Props {
    value?: string;
    label: string;
    /** ID unico desta instancia — usado pelo pai para evitar capturas simultaneas. */
    captureId: string;
    /** ID que esta capturando atualmente (controlado pelo pai). */
    activeCaptureId?: string | null;
    onCaptureStart?: (id: string) => void;
    onCaptureEnd?: () => void;
  }

  let {
    value = $bindable(""),
    label,
    captureId,
    activeCaptureId = null,
    onCaptureStart,
    onCaptureEnd,
  }: Props = $props();

  let capturing = $derived(activeCaptureId === captureId);

  function startCapture() {
    onCaptureStart?.(captureId);
  }

  function onKeydown(e: KeyboardEvent) {
    if (!capturing) return;
    e.preventDefault();
    e.stopPropagation();

    // Ignore lone modifier keys
    if (["Control", "Alt", "Shift", "Meta"].includes(e.key)) return;

    const parts: string[] = [];
    if (e.ctrlKey) parts.push("Ctrl");
    if (e.altKey) parts.push("Alt");
    if (e.shiftKey) parts.push("Shift");
    if (e.metaKey) parts.push("Meta");

    let key = e.key === " " ? "Space" : e.key;
    if (key.length === 1) key = key.toUpperCase();
    parts.push(key);

    value = parts.join("+");
    onCaptureEnd?.();
  }

  function onBlur() {
    if (capturing) onCaptureEnd?.();
  }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="flex items-center justify-between">
  <span class="text-sm text-[var(--text-secondary)]">{label}</span>
  <button
    onclick={startCapture}
    onblur={onBlur}
    class="px-4 py-2 text-sm font-mono rounded-[var(--radius-md)] border min-w-[150px] text-center
      transition-all duration-[120ms]
      {capturing
        ? 'border-[var(--accent-blue)] bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] animate-pulse'
        : 'border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-primary)] hover:border-[var(--accent-blue)]'}"
  >
    {capturing ? "Pressione..." : value}
  </button>
</div>
