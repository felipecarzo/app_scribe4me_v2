# HANDOFF — Scribe4me v2.0

## Meta

- **Data:** 2026-04-12
- **Branch:** main
- **Ultimo commit:** (inicial)
- **Agente:** Claude Opus 4.6
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Scribe4me v2.0 — rewrite com Tauri + Svelte + Python sidecar.
Sprint 1 em andamento: scaffold criado, falta validar build e fazer commit inicial.

## Task em andamento

T1-07 — npm install + cargo check (validar que tudo compila)

## Proximo passo exato

1. Rodar `npm install` para instalar dependencias JS
2. Rodar `cargo check` no src-tauri para validar Rust
3. Criar CLAUDE.md com regras do projeto
4. Git init + commit inicial
5. Criar repo no GitHub e push

## Arquivos relevantes

- `src/` — Frontend Svelte (App, Settings, StatusBar, store, sidecar bridge)
- `src-tauri/` — Backend Rust (tray, menu, sidecar spawn)
- `sidecar/` — Backend Python (JSON-RPC, sera migrado do v1)
- `docs/ROADMAP.md` — 6 sprints planejadas

## Estado do ROADMAP

| Sprint | Status |
|--------|--------|
| Sprint 1 — Fundacao | EM ANDAMENTO (6/9 concluidos) |
| Sprint 2 — Sidecar Real | PLANEJADO |
| Sprint 3 — Tray + Hotkeys | PLANEJADO |
| Sprint 4 — Settings Premium | PLANEJADO |
| Sprint 5 — Overlay Realtime | PLANEJADO |
| Sprint 6 — Build/Release | PLANEJADO |
