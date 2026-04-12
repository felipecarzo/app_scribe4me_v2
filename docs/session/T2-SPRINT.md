# Sprint 2 — Sidecar Real: Plano de Execucao

> Criado em: 2026-04-12 | Agente: Claude Opus 4.6

## Ordem de execucao

1. **T2-08** postprocess.py — copy verbatim, zero deps
2. **T2-01** config.py — foundation, replace platform imports
3. **T2-02** hardware.py — CUDA/GPU/RAM detection
4. **T2-03** recorder.py — sounddevice recording
5. **T2-04** transcriber.py — faster-whisper local
6. **T2-05** transcriber_api.py — OpenAI/Groq/Gemini/Deepgram
7. **T2-06** realtime_manager.py — Deepgram WebSocket
8. **T2-07** clipboard.py — pyperclip (paste simulation -> Rust)
9. **T2-09** Rust sidecar spawn — SidecarManager, stdin/stdout bridge
10. **T2-10** TS bridge — replace mocks with real Tauri invokes
11. **T2-11** Integration tests — subprocess JSON-RPC

## Decisoes arquiteturais

- **pynput REMOVIDO** — paste simulation via Rust (Tauri side)
- **platform module REMOVIDO** — inline _get_config_dir() helper
- **Long ops (model load, transcribe)** — run in background threads, emit events
- **pyperclip** mantido para clipboard copy
- **requirements.txt** — remover pynput, Pillow; adicionar pyperclip

## Riscos

1. stdin/stdout blocking — dispatcher precisa de thread pool
2. Model loading (5-15s) — deve rodar em thread separada
3. Dev vs prod sidecar spawn — python vs PyInstaller binary
