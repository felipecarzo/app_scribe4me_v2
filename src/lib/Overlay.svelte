<script lang="ts">
  import { fly, fade } from "svelte/transition";
  import { cubicOut } from "svelte/easing";
  import { listen } from "@tauri-apps/api/event";
  import Pill from "./components/Pill.svelte";

  type OverlayStatus = "recording" | "transcribing";

  let text = $state("");
  let status = $state<OverlayStatus>("recording");
  let visible = $state(false);
  let codeMode = $state(false);
  let clearTimer: ReturnType<typeof setTimeout> | null = null;

  // Listen for sidecar events — broadcast from Rust to all windows
  $effect(() => {
    let cleanup: (() => void) | null = null;

    listen<{ event: string; data: Record<string, unknown> }>(
      "sidecar-event",
      (ev) => {
        const { event, data } = ev.payload;

        if (event === "profile_changed") {
          codeMode = (data.code_mode as boolean) ?? false;
        } else if (event === "realtime_text") {
          text = (data.text as string) ?? "";
        } else if (event === "status_change") {
          const s = data.status as string;
          if (s === "recording") {
            // Cancel any pending text-clear from previous session
            if (clearTimer !== null) { clearTimeout(clearTimer); clearTimer = null; }
            status = "recording";
            text = "";
            visible = true;
          } else if (s === "transcribing") {
            if (clearTimer !== null) { clearTimeout(clearTimer); clearTimer = null; }
            status = "transcribing";
            visible = true;
          } else {
            // idle, done, error — hide overlay and clear text after exit animation
            visible = false;
            clearTimer = setTimeout(() => { text = ""; clearTimer = null; }, 420);
          }
        }
      }
    ).then((fn) => {
      cleanup = fn;
    });

    return () => cleanup?.();
  });
</script>

<div class="root">
  {#if visible}
    <div
      class="pill-wrapper"
      in:fly={{ y: 18, duration: 260, easing: cubicOut }}
      out:fade={{ duration: 360 }}
    >
      <Pill {text} {status} {codeMode} />
    </div>
  {/if}
</div>

<style>
  .root {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    width: 100vw;
    height: 100vh;
    padding-bottom: 6px;
    background: transparent;
    pointer-events: none;
    overflow: hidden;
  }

  .pill-wrapper {
    pointer-events: none;
  }
</style>
