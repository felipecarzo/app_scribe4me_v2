<script lang="ts">
  interface Props {
    text?: string;
    status?: "recording" | "transcribing";
    codeMode?: boolean;
  }

  let { text = "", status = "recording", codeMode = false }: Props = $props();
</script>

<div class="pill" data-status={status}>
  <span class="dot"></span>
  {#if codeMode}
    <span class="code-badge">CODE</span>
  {/if}
  <span class="label">{text || (status === "transcribing" ? "Transcrevendo..." : "Ouvindo...")}</span>
</div>

<style>
  .pill {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 14px 22px;
    border-radius: 999px;

    /* Glassmorphism */
    background: rgba(10, 17, 35, 0.82);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.10);
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.55),
      0 0 0 1px rgba(255, 255, 255, 0.03) inset;

    color: #f1f5f9;
    font-family: "Segoe UI", "Inter", system-ui, -apple-system, sans-serif;
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    max-width: 400px;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    background: #ef4444;
    animation: pulse-dot 1.2s ease-in-out infinite;
    transition: background 300ms ease;
  }

  [data-status="transcribing"] .dot {
    background: #f59e0b;
  }

  .label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .code-badge {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #60a5fa;
    background: rgba(96, 165, 250, 0.15);
    border: 1px solid rgba(96, 165, 250, 0.25);
    border-radius: 4px;
    padding: 1px 5px;
    flex-shrink: 0;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.45; transform: scale(0.82); }
  }
</style>
