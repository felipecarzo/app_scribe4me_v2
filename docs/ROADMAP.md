# ROADMAP — Scribe4me v2.0 (Tauri + Svelte)

> Atualizado em: 2026-04-12

---

## Sprint 1 — Fundacao (Scaffold + Sidecar)

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T1-01 | Scaffold Tauri + Svelte + Tailwind | CONCLUIDO | Estrutura base, vite, tsconfig |
| T1-02 | Tray icon nativo (Rust) + menu contexto | CONCLUIDO | Show/Quit, click esquerdo abre window |
| T1-03 | Protocolo JSON-RPC sidecar (Python) | CONCLUIDO | stdin/stdout, request/response/event |
| T1-04 | Settings UI Svelte (4 abas) | CONCLUIDO | Geral, Atalhos, Prompt, API |
| T1-05 | Store reativo (Svelte 5 runes) | CONCLUIDO | appState com status/backend/model |
| T1-06 | Sidecar bridge TypeScript | CONCLUIDO | sidecar.ts com send/on/handleMessage |
| T1-07 | npm install + cargo check + verificar build | CONCLUIDO | npm 0 vulns, cargo 3 warnings dead_code (esperado) |
| T1-08 | Git init + commit inicial + push | CONCLUIDO | 218efb9, pushed to origin/main |
| T1-09 | CLAUDE.md + governanca do projeto | CONCLUIDO | CLAUDE.md + .gitignore atualizado |

---

## Sprint 2 — Sidecar Real (Python backend conectado)

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T2-01 | Migrar config.py do v1 para sidecar | CONCLUIDO | Cross-platform config dir, atomic write, thread-safe |
| T2-02 | Migrar hardware.py do v1 | CONCLUIDO | Inline _get_ram_mb(), recommend_model respeita large-v3 para PT |
| T2-03 | Migrar recorder.py do v1 | CONCLUIDO | Constructor args (sem Config obj), chunk_callback |
| T2-04 | Migrar transcriber.py (Whisper local) | CONCLUIDO | Constructor args, CUDA fallback, thread-safe |
| T2-05 | Migrar transcriber_api.py (backends) | CONCLUIDO | OpenAI/Groq/Gemini/Deepgram, Gemini language-aware |
| T2-06 | Migrar realtime_manager.py (Deepgram WS) | CONCLUIDO | WebSocket streaming, JSON-RPC events |
| T2-07 | Migrar clipboard.py (output handler) | CONCLUIDO | pyperclip only, paste simulation -> Rust side |
| T2-08 | Migrar postprocess.py | CONCLUIDO | Verbatim copy, 20 unit tests |
| T2-09 | Integrar sidecar spawn no Tauri (Rust) | CONCLUIDO | SidecarManager, stdin/stdout bridge, event forwarding |
| T2-10 | Bridge completa TS <-> Python | CONCLUIDO | Tauri invoke + listen, typed API methods |
| T2-11 | Testes de integracao sidecar | CONCLUIDO | 10 integration tests + 20 unit tests, all green |

---

## Sprint 3 — Tray + Hotkeys + Estados

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T3-01 | Global shortcuts via Tauri plugin | PLANEJADO | PTT, Toggle, Cancel, Quit |
| T3-02 | Tray icon estados (5 cores/animacoes) | PLANEJADO | idle/loading/recording/transcribing/done |
| T3-03 | Tray menu dinamico (backend, modelo) | PLANEJADO | Atualiza labels com estado atual |
| T3-04 | Notificacoes nativas | PLANEJADO | Via Tauri notification plugin |
| T3-05 | Hotkey capture UI (Svelte) | PLANEJADO | Captura de atalhos customizados |
| T3-06 | Sincronizacao estado Tray <-> UI <-> Sidecar | PLANEJADO | Eventos bidirecionais |

---

## Sprint 4 — Settings UI Premium

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T4-01 | Design system completo (tokens, components) | PLANEJADO | Tailwind + CSS vars |
| T4-02 | Animacoes e transicoes | PLANEJADO | Tab switch, state changes, micro-interactions |
| T4-03 | Hotkey capture funcional no Svelte | PLANEJADO | Keyboard listener + display |
| T4-04 | Validacao de API keys inline | PLANEJADO | Test connection antes de salvar |
| T4-05 | Dark/Light mode toggle | PLANEJADO | Detectar OS preference |
| T4-06 | Onboarding first-run | PLANEJADO | Wizard de configuracao inicial |

---

## Sprint 5 — Overlay Realtime

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T5-01 | Window overlay transparente (Tauri) | PLANEJADO | Decorations false, always on top |
| T5-02 | Pill/Dynamic Island design (Svelte) | PLANEJADO | Glassmorphism, bordas arredondadas |
| T5-03 | Texto parcial streaming do sidecar | PLANEJADO | Eventos realtime_text |
| T5-04 | Animacao de entrada/saida | PLANEJADO | Slide up, fade out |
| T5-05 | Posicionamento inteligente | PLANEJADO | Bottom center, evitar taskbar |

---

## Sprint 6 — Build, Release e Polimento

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T6-01 | PyInstaller sidecar build (Windows) | PLANEJADO | scribe4me-sidecar.exe |
| T6-02 | Tauri bundle Windows (MSI/NSIS) | PLANEJADO | Com sidecar embutido |
| T6-03 | Tauri bundle macOS (DMG) | PLANEJADO | CI GitHub Actions |
| T6-04 | Tauri bundle Linux (AppImage/deb) | PLANEJADO | CI GitHub Actions |
| T6-05 | CI pipeline completo | PLANEJADO | Build + test + release |
| T6-06 | README + portfolio update | PLANEJADO | Screenshots, features |
| T6-07 | Performance profiling | PLANEJADO | Startup time, memory usage |
| T6-08 | Testes E2E | PLANEJADO | Playwright ou similar |

---

## Backlog

| ID | Task | Status |
|----|------|--------|
| BL-01 | Suporte Wayland nativo (Linux) | FUTURO |
| BL-02 | i18n (EN/ES/FR) | FUTURO |
| BL-03 | Plugin system para novos backends | FUTURO |
| BL-04 | Audio history / replay | FUTURO |
| BL-05 | LLM rewrite (reformular texto ditado) | FUTURO |

---

_Ultima atualizacao: 2026-04-12 — Sprint 2 concluida (11/11)_
