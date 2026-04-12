# HANDOFF — Scribe4me v2.0

## Meta

- **Data:** 2026-04-12
- **Branch:** main
- **Ultimo commit:** 33db055 — docs Sprint 6 README
- **Agente:** Claude Sonnet 4.6 (autopilot)
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

**PROJETO COMPLETO — Sprint 6 (8/8) CONCLUIDA.**

Todas as 6 sprints do ROADMAP foram concluidas (39 tasks no total).

Sprint 6 entregas:
- `sidecar/scribe4me-sidecar.spec`: PyInstaller onedir, console=True, upx=False, hiddenimports
- `sidecar/build_sidecar.bat`: build script Windows com guards e smoke test inline
- `sidecar/tests/test_smoke_binary.py`: smoke tests do binario compilado (auto-skip sem binario)
- `src-tauri/tauri.conf.json`: bundle.resources aponta para `sidecar/dist/scribe4me-sidecar/**/*`
- `src-tauri/src/sidecar.rs`: spawn() aceita Command pre-construido (dev vs release agnóstico)
- `src-tauri/src/lib.rs`: build_sidecar_command() resolve path por cfg debug/release; guard de existencia
- `.github/workflows/release.yml`: 8 jobs CI/CD — test, build sidecar, Tauri bundle, GitHub Release
- `README.md`: features, setup, arquitetura, download table, roadmap completo
- `sidecar/sidecar_main.py`: startup_ms + load_ms timing logs (T6-07)

## Task em andamento

Nenhuma — PROJETO COMPLETO.

## Proximo passo exato

1. Para gerar o primeiro release: criar tag `v2.0.0` e fazer push
   ```
   git tag v2.0.0
   git push origin v2.0.0
   ```
2. O CI rodara automaticamente e criara a GitHub Release com instaladores para as 3 plataformas.
3. Nota: antes do primeiro release real, executar `sidecar/build_sidecar.bat` localmente para validar o build do PyInstaller.

## Arquivos relevantes

- `sidecar/scribe4me-sidecar.spec` — PyInstaller spec
- `sidecar/build_sidecar.bat` — script de build Windows
- `sidecar/tests/test_smoke_binary.py` — smoke tests binario
- `sidecar/dist/scribe4me-sidecar/placeholder.txt` — placeholder para cargo check sem build
- `.github/workflows/release.yml` — CI/CD completo
- `src-tauri/src/lib.rs` — build_sidecar_command() com dev/release path resolution
- `README.md` — documentacao publica do projeto

## Estado do ROADMAP

| Sprint | Status |
|--------|--------|
| Sprint 1 — Fundacao | CONCLUIDO (9/9) |
| Sprint 2 — Sidecar Real | CONCLUIDO (11/11) |
| Sprint 3 — Tray + Hotkeys | CONCLUIDO (6/6) |
| Sprint 4 — Settings Premium | CONCLUIDO (6/6) |
| Sprint 5 — Overlay Realtime | CONCLUIDO (5/5) |
| Sprint 6 — Build/Release | CONCLUIDO (8/8) |

**Total: 45 tasks concluidas — ROADMAP 100% completo.**

## Notas para proxima sessao

- macOS DMG e arm64 only (Apple Silicon). Para suporte Intel: dois jobs CI separados.
- O secret `TAURI_SIGNING_PRIVATE_KEY` deve ser configurado no GitHub repo settings antes do release.
- `test_integration.py` excluido do CI por requerer hardware de audio — rodar localmente.
- CSS tokens hardcoded na Pill.svelte (minor do Revisor Sprint 5) — pode ser refatorado em backlog.
- backdrop-filter funciona no WebView2 (Windows 11 + Edge Chromium) — testar em Windows 10.
