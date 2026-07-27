# HANDOFF — Scribe4me v2.0

## Meta

- **Data:** 2026-07-27
- **Branch:** feat/port-beta-features
- **Ultimo commit:** 056e2be — fix(window): tauri-plugin-single-instance evita 2 processos rodando
- **Agente:** Claude Sonnet 5
- **Maquina:** ALIENWARE-LIPE (Windows 11)

## Estado do projeto

Sessao longa: retomou onde a sessao anterior parou (Sprint 7 — Revisor + 5 fixes de seguranca/correcao,
ja commitados no HANDOFF anterior mas **ainda nao commitados no git** — segue tudo como diff local).
Depois disso, foi pra teste manual do app (`npm run tauri dev`) com o Felipe, corrigindo bugs reportados
ao vivo, e terminou empacotando o instalador Windows (MSI + NSIS) — Sprint 8, ver ROADMAP.

**IMPORTANTE:** nenhum commit de codigo foi feito nesta sessao. Tudo abaixo esta como working tree diff,
23 arquivos modificados. `/end-session` nao commita codigo — so documentacao. O commit do codigo (Sprint 7
+ Sprint 8) esta pendente de aprovacao explicita do Felipe.

## Task em andamento

**Sprint 8 aplicada, ultimo fix (T8-09, console window) em teste no momento em que a sessao encerrou.**

Sequencia de bugs reportados pelo Felipe testando o app empacotado, na ordem:
1. Drag da janela nao funcionava, janela "presa" — fix: permission `core:window:allow-start-dragging` faltando.
2. Hotkeys nao respondiam — fix: registro batch all-or-nothing trocado por individual.
3. Dois icones na tray ao abrir — fix: `trayIcon` duplicado (config + codigo), removida a declaracao do config.
4. Icones feios (bolinha solida) — trocados por glyph headset+mic desenhado via PIL (tray + app icon).
5. Overlay mostrando "..." e parando de atualizar — fix: `on_partial`/`on_final` no `realtime_manager.py`
   paravam de mandar so o trecho atual da fala, nao o historico acumulado (que estourava o `max-width:400px`
   da Pill e o CSS truncava).
6. App instalado nao abria (crash silencioso) — causa: `bundle.resources` no `tauri.conf.json` usava glob
   com `../`, e o Tauri preservava a estrutura de pasta (virou `_up_\sidecar\dist\...` em vez de
   `scribe4me-sidecar\` na raiz dos resources) — o binario do sidecar nunca era encontrado. Fix: mapeamento
   explicito `{origem: destino}` no `resources`.
7. **[EM TESTE — resultado nao confirmado]** App instalado abria um PowerShell/console vazio junto, overlay
   as vezes nao aparecia, app fechava inesperadamente durante gravacao, e apareciam 2 icones na taskbar ao
   ativar gravacao. Causa suspeita: binario PyInstaller do sidecar e `console=True` (proposital p/ debug) —
   em release, como o processo pai (`scribe4me.exe`) e GUI subsystem sem console proprio, o Windows abre uma
   janela de console visivel pro filho (nao acontecia em dev pois o console e herdado do terminal de
   `cargo run`). A hipotese e que essa janela de console (que aparece na taskbar, rouba foco) explicava os
   outros 3 sintomas em cascata. Fix aplicado: `CREATE_NO_WINDOW` via `CommandExt::creation_flags` no spawn
   do sidecar (`src-tauri/src/sidecar.rs`). Rebuild feito, instalador relancado — **a sessao encerrou antes
   do Felipe confirmar se resolveu**.

## Proximo passo exato

1. **Perguntar ao Felipe** se o rebuild com `CREATE_NO_WINDOW` resolveu os 4 sintomas do item 7 acima
   (console popup, overlay sem texto, crash, 2 icones na taskbar). Se nao resolveu, investigar mais fundo
   (pode ser causa distinta do console — nao foi possivel confirmar a hipotese nesta sessao).
2. Se confirmado ok: revisar os 23 arquivos modificados (`git status`) e pedir aprovacao do Felipe pra
   commitar (Sprint 7 correcoes de seguranca + Sprint 8 UX/empacotamento).
3. Apos commit: decidir merge `feat/port-beta-features` -> `main` (ainda nao rodou pipeline completo
   Revisor -> Felipe -> SM pros commits novos desta sessao).
4. `npm audit`: 4 vulnerabilidades pendentes de investigacao (1 moderate, 3 high) — ainda nao investigado.
5. `vite.config.ts` porta mudada de 1420 para 5420 (Windows reserva 1357-1456 nesta maquina especifica —
   Hyper-V/WSL exclusion range). Isso e config de ambiente local, nao logica do app; avaliar se deve ficar
   assim no repo ou virar variavel de ambiente/override local nao commitado.

## Arquivos relevantes (working tree, nao commitados)

- `src-tauri/src/sidecar.rs` — `CREATE_NO_WINDOW` (item 7, em teste)
- `src-tauri/src/hotkeys.rs` — registro individual de shortcuts (`register_one`)
- `src-tauri/src/lib.rs` — `visible()` so em debug_assertions, tray sem duplicacao
- `src-tauri/capabilities/default.json` — `core:window:allow-start-dragging`, `shell:allow-open`
- `src-tauri/tauri.conf.json` — `resources` mapeado explicito, `productName`/`title` "Scribe4me v2", sem `trayIcon` duplicado
- `src-tauri/icons/*` — icones novos (tray 6 estados + app icon)
- `sidecar/realtime_manager.py` — fix do overlay truncando texto
- `sidecar/profiles.py`, `sidecar/sidecar_main.py` — fixes de seguranca do Revisor (Sprint 7)
- `src/lib/Settings.svelte` — backend selector movido pra aba Geral, botao "Pegar chave"
- `docs/ROADMAP.md` — Sprint 8 documentada

## Estado do ROADMAP

| Sprint | Status |
|--------|--------|
| Sprint 1 — Fundacao | CONCLUIDO (9/9) |
| Sprint 2 — Sidecar Real | CONCLUIDO (11/11) |
| Sprint 3 — Tray + Hotkeys | CONCLUIDO (6/6) |
| Sprint 4 — Settings Premium | CONCLUIDO (6/6) |
| Sprint 5 — Overlay Realtime | CONCLUIDO (5/5) |
| Sprint 6 — Build/Release | CONCLUIDO (8/8) |
| Sprint 7 — Port Beta Features + Estabilizacao | CONCLUIDO (8/8) — nao commitado |
| Sprint 8 — UX Fixes + Empacotamento Windows | 9/9 codigo pronto, 1 em teste — nao commitado |

## Notas para proxima sessao

- **Nenhum commit de codigo feito** — HANDOFF/ROADMAP sao os unicos arquivos versionados nesta sessao.
- Instalador gerado em: `src-tauri/target/release/bundle/{msi,nsis}/Scribe4me v2_2.0.0_*` (nao versionado, so local).
- App instalado em: `C:\Users\<user>\AppData\Local\Scribe4me v2\`.
- Branch `feat/port-beta-features` nao passou por Revisor pros commits desta sessao ainda.
- macOS DMG e arm64 only (Apple Silicon). Para suporte Intel: dois jobs CI separados.
- O secret `TAURI_SIGNING_PRIVATE_KEY` deve ser configurado no GitHub repo settings antes do release.
- `test_integration.py` excluido do CI por requerer hardware de audio — rodar localmente.
- backdrop-filter funciona no WebView2 (Windows 11 + Edge Chromium) — testar em Windows 10.
