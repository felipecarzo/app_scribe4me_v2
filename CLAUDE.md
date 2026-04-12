# CLAUDE.md — Scribe4me v2.0

## Sobre o projeto

Scribe4me v2.0 — app desktop speech-to-text com UI premium.
Stack: Tauri v2 (Rust) + Svelte 5 + Tailwind CSS v4 + Python sidecar (faster-whisper).

## Estrutura

```
src/              → Frontend Svelte (UI)
src-tauri/        → Backend Rust (Tauri — tray, hotkeys, window management)
sidecar/          → Backend Python (audio, STT, APIs, clipboard)
docs/             → Governanca (ROADMAP, HANDOFF, session files, daily logs)
```

## Comandos de desenvolvimento

```bash
npm run dev          # Vite dev server (frontend only, sem Tauri)
npm run tauri dev    # Tauri dev mode (frontend + Rust + sidecar)
npm run build        # Build frontend para produção
npm run tauri build  # Build completo (MSI/DMG/AppImage)
npm run check        # Type check Svelte/TS
cargo check          # Verifica compilacao Rust (dentro de src-tauri/)
cargo clippy         # Lint Rust
```

## Regras do projeto

- **Python sidecar** comunica via JSON-RPC sobre stdin/stdout (JSON lines)
- **Nunca** importar tkinter, customtkinter ou pystray — toda UI é Svelte
- **Nunca** sugerir modelos Whisper menores que large-v3 — qualidade em PT-BR cai demais
- **Hotkeys globais** via Tauri global-shortcut plugin, não pynput
- **Tray icon** nativo via Tauri, não pystray
- **Config** persistida em JSON pelo sidecar Python (compatível com v1)

## Pipeline de qualidade

```
Planner → implementa → Tester → Revisor → Felipe → SM → commit
```

- Tester obrigatorio apos qualquer modificacao de codigo
- Revisor obrigatorio antes de merge/push
- ROADMAP atualizado pelo Scrum Manager apos cada task concluida

## Convenções

- Commits: `tipo(escopo): descricao` (feat, fix, refactor, docs, test, ci)
- Branches: `feat/T{ID}-descricao` para tasks do ROADMAP
- Svelte: Svelte 5 runes ($state, $derived, $effect), não stores legados
- CSS: Tailwind utility-first, CSS vars para design tokens
- Rust: snake_case, clippy clean
- Python: snake_case, type hints, docstrings

## Contexto v1

O Scribe4me v1.5.0 (Python puro + tkinter) está em `../app_scribe4me/`.
O sidecar reutiliza os módulos backend do v1 (recorder, transcriber, config, etc).
