# Scribe4me v2.0

> Speech-to-text desktop app — always-on tray, global hotkeys, realtime overlay.

Built with **Tauri v2** (Rust) + **Svelte 5** + **Python sidecar** (faster-whisper).

---

## Features

- **Push-to-talk** (`Ctrl+Alt+H`) — hold to record, release to transcribe
- **Toggle record** (`Ctrl+Alt+T`) — start/stop with one press
- **Realtime overlay** — glassmorphism pill floats above all windows while recording
- **Local STT** — faster-whisper large-v3, CUDA + CPU fallback (no cloud required)
- **API backends** — OpenAI Whisper, Groq, Gemini, Deepgram (streaming)
- **System tray** — 6 status icons, dynamic menu, no dock entry
- **Output modes** — clipboard copy or cursor paste simulation
- **Dark/Light/System theme** — zero-FOWT with inline script
- **First-run wizard** — hardware detection, model recommendation, output mode choice
- **Settings UI** — 4 tabs, inline API key validation with latency badge
- **Custom prompt** — post-process transcription via LLM

---

## Download

| Platform | Installer | Requirement |
|----------|-----------|-------------|
| Windows 11 | `.msi` / `.exe` (NSIS) | WebView2 (built-in on Win 11) |
| macOS 13+ | `.dmg` | Apple Silicon (M1+) |
| Linux | `.AppImage` / `.deb` | libwebkit2gtk-4.1 |

> macOS Intel not supported — `ctranslate2` wheels are not universal. Community PRs welcome.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop shell | Tauri v2 (Rust) |
| Frontend | Svelte 5 (runes), Tailwind CSS v4 |
| Backend | Python 3.12, faster-whisper, sounddevice |
| Local STT | faster-whisper + CTranslate2 (CUDA / CPU) |
| Packaging | PyInstaller (onedir) + Tauri bundle |
| CI/CD | GitHub Actions |

---

## Development

### Prerequisites

- [Node.js 20+](https://nodejs.org)
- [Rust stable](https://rustup.rs)
- [Python 3.12+](https://python.org)
- [Tauri CLI](https://tauri.app/start/prerequisites/) — `cargo install tauri-cli`

### Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_USER/app_scribe4me_v2.git
cd app_scribe4me_v2

# 2. Frontend deps
npm install

# 3. Python sidecar deps
cd sidecar
pip install -r requirements.txt
cd ..

# 4. Dev mode (hot-reload)
npm run tauri:dev
```

### Available commands

```
npm run dev          # Vite dev server only (frontend)
npm run tauri:dev    # Full dev mode (Tauri + sidecar)
npm run build        # Frontend production build
npm run tauri:build  # Full release build (requires sidecar binary)
npm run check        # TypeScript + Svelte type check
```

```
cd src-tauri
cargo check          # Rust compile check
cargo clippy         # Rust lint
```

```
cd sidecar
python -m pytest tests/test_postprocess.py -v   # Unit tests (no hardware needed)
python -m pytest tests/test_integration.py  -v  # Integration tests (needs microphone)
```

### Building for release

```bash
# 1. Build Python sidecar (Windows)
cd sidecar
build_sidecar.bat

# 2. Build Tauri app
cd ..
npm run tauri:build
```

> The sidecar binary must exist at `sidecar/dist/scribe4me-sidecar/` before running `tauri build`.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Tauri (Rust)                                   │
│  ┌──────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  Tray    │  │  Hotkeys    │  │  Overlay  │  │
│  │  icon    │  │  (global)   │  │  window   │  │
│  └──────────┘  └─────────────┘  └───────────┘  │
│         │              │              │          │
│  ┌──────┴──────────────┴──────────────┴──────┐  │
│  │  SidecarManager (JSON-RPC bridge)         │  │
│  └────────────────────┬──────────────────────┘  │
└───────────────────────│─────────────────────────┘
                        │ stdin/stdout (JSON lines)
┌───────────────────────┴─────────────────────────┐
│  Python sidecar                                 │
│  ┌──────────┐  ┌─────────────┐  ┌───────────┐  │
│  │  Config  │  │  Recorder   │  │ Clipboard │  │
│  └──────────┘  └─────────────┘  └───────────┘  │
│  ┌──────────┐  ┌─────────────────────────────┐  │
│  │ Hardware │  │  Transcriber (local/API)    │  │
│  └──────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Svelte 5 frontend (WebView2 / WebKit)          │
│  Settings UI · Onboarding wizard · Theme toggle │
└─────────────────────────────────────────────────┘
```

---

## Roadmap

- [x] Sprint 1 — Scaffold (Tauri + Svelte + sidecar protocol)
- [x] Sprint 2 — Python sidecar (audio, Whisper, API backends)
- [x] Sprint 3 — Tray + global hotkeys + state sync
- [x] Sprint 4 — Settings UI premium (theme, onboarding, API validation)
- [x] Sprint 5 — Realtime overlay (glassmorphism pill)
- [x] Sprint 6 — Build, release, CI/CD

---

## License

MIT
