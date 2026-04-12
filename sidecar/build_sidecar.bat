@echo off
setlocal enabledelayedexpansion

echo === Scribe4me Sidecar Build ===
echo.

:: Verifica se pyinstaller esta disponivel no PATH
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: pyinstaller nao encontrado.
    echo       Instale com: pip install pyinstaller
    exit /b 1
)

:: Garante que estamos no diretorio do script (sidecar/)
cd /d "%~dp0"

:: Limpa builds anteriores para evitar artefatos obsoletos
if exist "dist\scribe4me-sidecar" (
    echo Limpando dist anterior...
    rmdir /s /q "dist\scribe4me-sidecar"
)
if exist "build\scribe4me-sidecar" (
    echo Limpando build cache anterior...
    rmdir /s /q "build\scribe4me-sidecar"
)

echo Executando PyInstaller...
echo.
pyinstaller scribe4me-sidecar.spec --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo ERRO: PyInstaller falhou com codigo %errorlevel%.
    exit /b 1
)

echo.
echo === Build concluido ===
echo Saida: %~dp0dist\scribe4me-sidecar\
echo.

:: Verifica que o executavel foi gerado
if exist "dist\scribe4me-sidecar\scribe4me-sidecar.exe" (
    echo OK: scribe4me-sidecar.exe encontrado.

    :: Smoke test: envia um ping JSON-RPC e verifica resposta
    echo.
    echo Executando smoke test...
    echo {"id":1,"method":"ping","params":{}} | "dist\scribe4me-sidecar\scribe4me-sidecar.exe" 2>nul | findstr /c:"pong" >nul
    if %errorlevel% equ 0 (
        echo OK: smoke test ping passou.
    ) else (
        echo AVISO: smoke test nao confirmou resposta pong.
        echo        Isso pode ocorrer se o sidecar precisar de dependencias de audio.
        echo        Execute manualmente para verificar.
    )
) else (
    echo ERRO: executavel nao encontrado em dist\scribe4me-sidecar\
    exit /b 1
)

echo.
echo Proximo passo: executar "npm run tauri build" na raiz do projeto.
exit /b 0
