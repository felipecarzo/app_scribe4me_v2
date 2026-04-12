# HANDOFF — Scribe4me v2.0

## Meta

- **Data:** 2026-04-12
- **Branch:** main
- **Ultimo commit:** (pending — Sprint 2 commit)
- **Agente:** Claude Opus 4.6
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Sprint 2 (Sidecar Real) CONCLUIDA — 11/11 tasks.
Todos os modulos Python do v1 migrados para o sidecar com adaptacoes:
- pynput removido (paste simulation -> Rust/Tauri)
- platform module substituido por helpers inline
- Thread safety: _state_lock protege globals mutaveis
- Config: atomic write com tmp+rename, _config_lock
- recommend_model: sempre large-v3 para PT-BR
- GeminiTranscriber: agora respeita parametro language
- 30 testes (20 unit + 10 integration), todos verdes

## Task em andamento

Nenhuma — Sprint 2 finalizada. Proximo: Sprint 3.

## Proximo passo exato

1. Iniciar Sprint 3 — Tray + Hotkeys + Estados
2. T3-01: Global shortcuts via Tauri plugin
3. Requer definicao das hotkeys e integracao com sidecar

## Arquivos relevantes

- `sidecar/` — 9 modulos Python migrados + sidecar_main.py (orquestrador)
- `src-tauri/src/sidecar.rs` — SidecarManager (spawn, stdin/stdout bridge)
- `src-tauri/src/lib.rs` — Tauri commands (sidecar_send) + event forwarding
- `src/lib/sidecar.ts` — SidecarBridge TypeScript (invoke + listen)
- `docs/ROADMAP.md` — Sprint 1+2 concluidas, Sprint 3 proximo

## Estado do ROADMAP

| Sprint | Status |
|--------|--------|
| Sprint 1 — Fundacao | CONCLUIDO (9/9) |
| Sprint 2 — Sidecar Real | CONCLUIDO (11/11) |
| Sprint 3 — Tray + Hotkeys | PLANEJADO |
| Sprint 4 — Settings Premium | PLANEJADO |
| Sprint 5 — Overlay Realtime | PLANEJADO |
| Sprint 6 — Build/Release | PLANEJADO |

## Notas para proxima sessao

- API keys ainda em plain text (config.json) — considerar keyring para Sprint 4
- Sidecar spawn em dev mode usa `python sidecar/sidecar_main.py` — prod usara PyInstaller binary (Sprint 6)
- Warnings de dead_code no Rust resolvidos (structs removidas)
