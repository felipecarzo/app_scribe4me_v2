# -*- mode: python ; coding: utf-8 -*-
# Scribe4me Sidecar — PyInstaller spec
#
# Modo: onedir (nao onefile) — faster-whisper exige acesso ao filesystem
# para carregar modelos CTranslate2 em runtime.
# console=True e OBRIGATORIO: o sidecar comunica via stdin/stdout JSON-RPC.
#
# Build: executar build_sidecar.bat (Windows) ou:
#   pyinstaller scribe4me-sidecar.spec --noconfirm

block_cipher = None

a = Analysis(
    ["sidecar_main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # audio
        "sounddevice",
        "soundfile",
        "cffi",
        "_cffi_backend",  # backend C da cffi — pyinstaller pode nao detectar automaticamente
        # whisper / ctranslate2
        "ctranslate2",
        "faster_whisper",
        "faster_whisper.transcribe",
        "faster_whisper.audio",
        "faster_whisper.feature_extractor",
        "faster_whisper.tokenizer",
        "faster_whisper.vad",
        # numpy
        "numpy",
        "numpy.core._methods",
        "numpy.lib.format",
        # clipboard
        "pyperclip",
        "pyperclip.handlers",
        # websocket (realtime Deepgram)
        "websocket",
        "websocket._core",
        "websocket._app",
        "websocket._abnf",
        "websocket._exceptions",
        "websocket._handshake",
        "websocket._http",
        "websocket._logging",
        "websocket._socket",
        "websocket._ssl_compat",
        "websocket._utils",
        # httpx (API backends)
        "httpx",
        "httpx._client",
        "httpcore",
        # stdlib extras que pyinstaller pode perder
        "urllib.request",
        "urllib.error",
        "urllib.parse",
        "json",
        "threading",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # UI libs banidas pelo projeto
        "tkinter",
        "tkinter.ttk",
        "customtkinter",
        "pystray",
        "pynput",
        # GUI frameworks desnecessarios
        "PyQt5",
        "PyQt6",
        "wx",
        "gi",
        # outros desnecessarios
        "matplotlib",
        "IPython",
        "jupyter",
        "PIL",
        "cv2",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="scribe4me-sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX desabilitado — pode corromper DLLs CUDA/CTranslate2
    console=True,  # OBRIGATORIO: JSON-RPC via stdin/stdout
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="scribe4me-sidecar",
)
