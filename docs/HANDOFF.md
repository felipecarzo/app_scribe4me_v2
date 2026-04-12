# HANDOFF — Scribe4me v2.0

## Meta

- **Data:** 2026-04-12
- **Branch:** main
- **Ultimo commit:** (pending — Sprint 3 commit)
- **Agente:** Claude Opus 4.6
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Sprint 3 (Tray + Hotkeys + Estados) CONCLUIDA — 6/6 tasks.
Principais entregas:
- Global shortcuts: PTT (press=start, release=stop), Toggle, Cancel, Quit
- Estado de gravacao via AtomicBool compartilhado entre hotkeys e tray menu
- 6 tray icons dinamicos (idle/loading/recording/transcribing/done/error)
- TrayMenuItems managed state para atualizacao dinamica de labels
- Notificacoes nativas via tauri-plugin-notification
- Config sync no init do sidecar bridge (onMount, nao $effect)
- Aba "atalhos customizados" removida (hotkeys hardcoded — customizacao planejada para Sprint 4)

Revisor: aprovado com ressalvas menores (N1: cancel sem guard, N2: shortcut.to_string() format, N3: onMount sem cleanup).

## Task em andamento

Nenhuma — Sprint 3 finalizada. Proximo: Sprint 4.

## Proximo passo exato

1. Iniciar Sprint 4 — Settings UI Premium
2. T4-01: Design system completo (tokens, components)
3. T4-03: Hotkey capture funcional (re-registro de shortcuts no Rust)

## Arquivos relevantes

- `src-tauri/src/hotkeys.rs` — Global shortcuts + AtomicBool IS_RECORDING
- `src-tauri/src/lib.rs` — TrayMenuItems, update_tray_icon, update_tray_info, sidecar event routing
- `src-tauri/icons/tray-*.png` — 6 icones de tray por estado
- `src/lib/sidecar.ts` — SidecarBridge com notify(), config load, updateTrayInfo
- `src/lib/Settings.svelte` — 3 abas (Geral, Prompt, API), onMount config sync
- `sidecar/` — 9 modulos Python + sidecar_main.py
- `src-tauri/src/sidecar.rs` — SidecarManager (spawn, stdin/stdout bridge)

## Estado do ROADMAP

| Sprint | Status |
|--------|--------|
| Sprint 1 — Fundacao | CONCLUIDO (9/9) |
| Sprint 2 — Sidecar Real | CONCLUIDO (11/11) |
| Sprint 3 — Tray + Hotkeys | CONCLUIDO (6/6) |
| Sprint 4 — Settings Premium | PLANEJADO |
| Sprint 5 — Overlay Realtime | PLANEJADO |
| Sprint 6 — Build/Release | PLANEJADO |

## Notas para proxima sessao

- Hotkeys sao hardcoded (Ctrl+Alt+H/T/C, Ctrl+Q) — Sprint 4 T4-03 deve implementar re-registro dinamico
- API keys ainda em plain text (config.json) — considerar keyring para Sprint 4
- Sidecar spawn em dev mode usa `python sidecar/sidecar_main.py` — prod usara PyInstaller binary (Sprint 6)
- Revisor N2: verificar manualmente se shortcut.to_string() match funciona em runtime
