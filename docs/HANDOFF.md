# HANDOFF — Scribe4me v2.0

## Meta

- **Data:** 2026-04-12
- **Branch:** main
- **Ultimo commit:** 5daadb2 — Sprint 4 completo
- **Agente:** Claude Opus 4.6 / Sonnet 4.6
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Sprint 4 (Settings UI Premium) CONCLUIDA — 6/6 tasks.
Principais entregas:
- Design system: tokens dark/light, componentes Button/Input reutilizaveis
- Animacoes: Svelte fade entre abas, spinner no save, transition-colors
- Hotkey capture funcional: HotkeyCapture com estado compartilhado no pai, re-registro via Rust
- Validacao API keys: badge inline com debounce, test_api_key RPC via urllib
- Dark/Light/System theme: [data-theme] CSS vars, ThemeToggle, anti-FOWT no index.html
- Onboarding wizard: 3 passos, detecta first-run via config.py

Revisor: aprovado com ressalvas — todos os 4 MAJORs corrigidos antes do commit.

## Task em andamento

Nenhuma — Sprint 4 finalizada. Proximo: Sprint 5.

## Proximo passo exato

1. Iniciar Sprint 5 — Overlay Realtime
2. T5-01: Window overlay transparente (Tauri) — decorations false, always on top
3. T5-02: Pill/Dynamic Island design (Svelte) — glassmorphism

## Arquivos relevantes

- `src/lib/components/` — 5 novos componentes (Button, Input, HotkeyCapture, ThemeToggle, Onboarding)
- `src/lib/Settings.svelte` — 4 abas, validacao API, hotkeys funcionais
- `src/App.svelte` — theme effect, condicional onboarding vs settings
- `src-tauri/src/hotkeys.rs` — HotkeyConfig+Lazy<Mutex>, reregister_shortcuts
- `sidecar/config.py` — is_first_run, mark_first_run_done
- `sidecar/sidecar_main.py` — test_api_key handler, theme/first_run em get/save_config

## Estado do ROADMAP

| Sprint | Status |
|--------|--------|
| Sprint 1 — Fundacao | CONCLUIDO (9/9) |
| Sprint 2 — Sidecar Real | CONCLUIDO (11/11) |
| Sprint 3 — Tray + Hotkeys | CONCLUIDO (6/6) |
| Sprint 4 — Settings Premium | CONCLUIDO (6/6) |
| Sprint 5 — Overlay Realtime | PLANEJADO |
| Sprint 6 — Build/Release | PLANEJADO |

## Notas para proxima sessao

- Sprint 5 exige nova janela Tauri (overlay transparente) — precisara de nova entrada em tauri.conf.json
- Texto parcial do Deepgram (realtime_text events) ja existe no sidecar — so precisa de UI
- `once_cell` adicionado como dep Rust (usado no HOTKEY_CONFIG lazy static)
- API keys ainda em plain text no config.json — considerar keyring em sprint futuro
