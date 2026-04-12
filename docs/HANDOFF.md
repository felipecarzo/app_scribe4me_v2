# HANDOFF — Scribe4me v2.0

## Meta

- **Data:** 2026-04-12
- **Branch:** main
- **Ultimo commit:** 17e640e — Sprint 5 completo
- **Agente:** Claude Sonnet 4.6
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Sprint 5 (Overlay Realtime) CONCLUIDA — 5/5 tasks.
Principais entregas:
- `overlay.rs`: WebviewWindow "overlay" always_on_top + transparent + focused(false) + ignore_cursor_events
- `Pill.svelte`: glassmorphism pill com backdrop-filter, pulse dot por status
- `Overlay.svelte`: escuta sidecar-event broadcast, controla visibilidade + texto
- Animacoes: in:fly(y=18, 260ms) + out:fade(360ms)
- Posicionamento: primary_monitor + scale_factor, 48px margin bottom

Revisor: aprovado com ressalvas — 3 MAJORs corrigidos antes do commit.

## Task em andamento

Nenhuma — Sprint 5 finalizada. Proximo: Sprint 6.

## Proximo passo exato

1. Iniciar Sprint 6 — Build, Release e Polimento
2. T6-01: PyInstaller sidecar build (Windows) — scribe4me-sidecar.exe
3. T6-02: Tauri bundle Windows (MSI/NSIS) com sidecar embutido

## Arquivos relevantes

- `src-tauri/src/overlay.rs` — WebviewWindow overlay, show/hide/position
- `src/lib/Overlay.svelte` — root component, sidecar event listener
- `src/lib/components/Pill.svelte` — glassmorphism pill visual
- `src/overlay.ts` + `overlay.html` — Vite entry separado para overlay
- `vite.config.ts` — multi-entry build (main + overlay)

## Estado do ROADMAP

| Sprint | Status |
|--------|--------|
| Sprint 1 — Fundacao | CONCLUIDO (9/9) |
| Sprint 2 — Sidecar Real | CONCLUIDO (11/11) |
| Sprint 3 — Tray + Hotkeys | CONCLUIDO (6/6) |
| Sprint 4 — Settings Premium | CONCLUIDO (6/6) |
| Sprint 5 — Overlay Realtime | CONCLUIDO (5/5) |
| Sprint 6 — Build/Release | PLANEJADO |

## Notas para proxima sessao

- Sprint 6 requer PyInstaller instalado: `pip install pyinstaller`
- O sidecar .spec file precisa incluir: sounddevice, ctranslate2, faster-whisper, pyperclip
- Tauri sidecar config: `src-tauri/tauri.conf.json` deve ter `bundle.externalBin` ou `sidecarBin`
- backdrop-filter funciona no WebView2 (Windows 11 + Edge Chromium) — testar em Windows 10
- CSS tokens hardcoded na Pill.svelte (Revisor minor) — pode ser refatorado no Sprint 6 polish
