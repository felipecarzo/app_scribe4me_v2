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
| T3-01 | Global shortcuts via Tauri plugin | CONCLUIDO | PTT (press/release), Toggle, Cancel, Quit via AtomicBool state |
| T3-02 | Tray icon estados (5 cores) | CONCLUIDO | 6 PNGs include_bytes!, idle/loading/recording/transcribing/done/error |
| T3-03 | Tray menu dinamico (backend, modelo) | CONCLUIDO | TrayMenuItems managed state, update_tray_info command |
| T3-04 | Notificacoes nativas | CONCLUIDO | tauri-plugin-notification, permission check, error/done/paste events |
| T3-05 | Settings UI (config sync) | CONCLUIDO | onMount config load, aba atalhos removida (hotkeys hardcoded por ora) |
| T3-06 | Sincronizacao estado Tray <-> UI <-> Sidecar | CONCLUIDO | sidecar event -> update_tray_icon -> set_recording -> menu/hotkey sync |

---

## Sprint 4 — Settings UI Premium

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T4-01 | Design system completo (tokens, components) | CONCLUIDO | Button/Input components, radius/transition tokens dark+light |
| T4-02 | Animacoes e transicoes | CONCLUIDO | Svelte fade entre abas, spinner no save, transition-colors |
| T4-03 | Hotkey capture funcional no Svelte | CONCLUIDO | HotkeyCapture+shared state, reregister_shortcuts Rust, update_shortcuts command |
| T4-04 | Validacao de API keys inline | CONCLUIDO | test_api_key RPC (urllib), Input badge, debounce 800ms |
| T4-05 | Dark/Light mode toggle | CONCLUIDO | [data-theme] tokens, ThemeToggle, anti-FOWT index.html |
| T4-06 | Onboarding first-run | CONCLUIDO | Wizard 3 passos, is_first_run/mark_done config.py |

---

## Sprint 5 — Overlay Realtime

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T5-01 | Window overlay transparente (Tauri) | CONCLUIDO | overlay.rs, always_on_top, skip_taskbar, focused(false), ignore_cursor_events |
| T5-02 | Pill/Dynamic Island design (Svelte) | CONCLUIDO | Pill.svelte glassmorphism, Overlay.svelte, overlay.html Vite entry |
| T5-03 | Texto parcial streaming do sidecar | CONCLUIDO | listen(sidecar-event), realtime_text → text, clearTimeout guard |
| T5-04 | Animacao de entrada/saida | CONCLUIDO | in:fly(y=18,260ms) + out:fade(360ms) |
| T5-05 | Posicionamento inteligente | CONCLUIDO | position_bottom_center com scale_factor, 48px margin |

---

## Sprint 6 — Build, Release e Polimento

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T6-01 | PyInstaller sidecar build (Windows) | CONCLUIDO | scribe4me-sidecar.spec + build_sidecar.bat |
| T6-02 | Tauri bundle Windows (MSI/NSIS) | CONCLUIDO | bundle.resources + build_sidecar_command() dev/release |
| T6-03 | Tauri bundle macOS (DMG) | CONCLUIDO | CI job build-tauri-macos (arm64 only — macos-14) |
| T6-04 | Tauri bundle Linux (AppImage/deb) | CONCLUIDO | CI job build-tauri-linux |
| T6-05 | CI pipeline completo | CONCLUIDO | .github/workflows/release.yml — 8 jobs, tag trigger |
| T6-06 | README + portfolio update | CONCLUIDO | README.md com features, setup, arquitetura, roadmap |
| T6-07 | Performance profiling | CONCLUIDO | startup_ms + load_ms logs no sidecar_main.py |
| T6-08 | Testes E2E | CONCLUIDO | test_smoke_binary.py — auto-skip sem binario, 6 casos |

---

## Sprint 7 — Port Beta Features + Estabilizacao Dev Mode

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T7-01 | Port profiles + voice coding do beta para v2 | CONCLUIDO | 293cc28 |
| T7-02 | Fix config plugins Tauri v2 (unit vs map) | CONCLUIDO | 0606a11, 60acc4e |
| T7-03 | Fix conexao sidecar Python em dev mode | CONCLUIDO | 5731628, 45d63ac, 9a4ed68 — PYTHONUNBUFFERED, encoding, log file diagnostico |
| T7-04 | 5 fixes criticos (3 auditorias paralelas) | CONCLUIDO | 21b2f3c |
| T7-05 | Fix capabilities overlay + global-shortcut | CONCLUIDO | d64dfed |
| T7-06 | Fix UI skipTaskbar + botao X + hide-on-save | CONCLUIDO | 4dfb431, edc101b |
| T7-07 | Fix hotkeys formato canonico CommandOrControl | CONCLUIDO | 70edb54 diag, c615164 fix |
| T7-08 | Fix window (hide nativo, skip_taskbar startup, single-instance) | CONCLUIDO | 067e54e, 9f4c7a4, 056e2be |

Branch `feat/port-beta-features`, 15 commits acima de `main` (9ea945f). Ainda nao mergeada.
Verificado em 2026-07-26: `cargo check` limpo, `npm run check` 0 erros (2 warnings a11y pre-existentes).

---

## Sprint 8 — UX Fixes + Empacotamento Windows

| ID | Task | Status | Notas |
|----|------|--------|-------|
| T8-01 | Fix drag da janela principal | CONCLUIDO | Faltava permission `core:window:allow-start-dragging` na ACL — `data-tauri-drag-region` ja existia no HTML mas era bloqueado silenciosamente |
| T8-02 | Fix registro de hotkeys (all-or-nothing) | CONCLUIDO | `on_shortcuts` batch abortava os 4 se 1 colidisse com outro app; reescrito para `on_shortcut` individual (register_one) — colisao em 1 nao derruba os outros |
| T8-03 | Fix tray icon duplicado | CONCLUIDO | `trayIcon` declarado em `tauri.conf.json` E criado programaticamente em `lib.rs` — dois mecanismos, dois icones. Removida a declaracao do config |
| T8-04 | Icones novos (tray + app) | CONCLUIDO | Placeholders eram bolinhas solidas de cor. Novos: glyph headset+mic desenhado via PIL, tray mantem cores por status, app icon com squircle+gradiente azul |
| T8-05 | Fix overlay truncando texto com "..." | CONCLUIDO | `on_partial`/`on_final` prefixavam texto acumulado desde o inicio da gravacao; Pill tem `max-width:400px;nowrap`, CSS truncava com "...". Agora manda so o trecho atual da fala |
| T8-06 | Botao "Pegar chave" nas API keys | CONCLUIDO | Abre a pagina de API key de cada provider no navegador (`shell:allow-open` + `@tauri-apps/plugin-shell`) |
| T8-07 | Rename para "Scribe4me v2" em toda a UI | CONCLUIDO | productName, window title, tray tooltip, header do App.svelte — evita confusao com o v1 (Python/tkinter) instalado na mesma maquina |
| T8-08 | Empacotamento Windows (MSI + NSIS) | CONCLUIDO | `build_sidecar.bat` (PyInstaller) + `npm run tauri build`. Fix critico: `resources` no config usava glob com `../`, Tauri preservava a estrutura (`_up_\sidecar\dist\...`) em vez de `scribe4me-sidecar\` na raiz — app crashava no primeiro boot com "Sidecar binary not found". Corrigido com mapeamento explicito `{origem: destino}` |
| T8-09 | Fix janela de console (PowerShell) abrindo junto | CONCLUIDO (codigo) — EM TESTE | Sidecar PyInstaller e `console=True` (proposital p/ debug); em release o processo pai (GUI subsystem) forca o Windows a abrir console visivel para o filho. Fix: `CREATE_NO_WINDOW` via `CommandExt::creation_flags` no spawn. Suspeita de que isso tambem explicava overlay nao aparecer e crash inesperado reportados pelo Felipe — rebuild feito, instalador relancado, **resultado do teste ainda nao confirmado nesta sessao** |

Pendente: confirmacao do Felipe que T8-09 resolveu os 3 sintomas (console popup, overlay sem texto, crash inesperado, 2 icones na taskbar ao gravar).

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

_Ultima atualizacao: 2026-07-27 — Sprint 8 (9/9 codigo, 1 item em teste) — empacotamento Windows funcional, fixes de UX aplicados, branch feat/port-beta-features ainda pendente merge_
