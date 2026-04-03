@echo off
REM Pipeline completa per la generazione del voice pack italiano CrewChief
REM Uso: scripts\build_all.bat [--install] [--voice NOME]

setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

set INSTALL=false
set VOICE=

:parse_args
if "%~1"=="" goto :start
if "%~1"=="--install" (set INSTALL=true& shift& goto :parse_args)
if "%~1"=="--voice" (set "VOICE=%~2"& shift& shift& goto :parse_args)
echo Uso: %~0 [--install] [--voice NOME]
exit /b 1

:start
echo === CrewChief ITA Voice Pack - Pipeline Completa ===
echo.

REM Step 1: Validazione lessico
echo [1/4] Validazione lessico...
if exist "lexicon\phrase_inventory_ita.csv" (
    echo   phrase_inventory_ita.csv trovato
) else (
    echo   ERRORE: phrase_inventory_ita.csv non trovato!
    echo   Esegui prima: python voice_generator\enrich_lexicon.py
    exit /b 1
)

python -m pytest tests\test_lexicon.py -v --tb=short 2>nul
if errorlevel 1 (
    echo   Warning: alcuni test lexicon falliti, continuo comunque
)

REM Step 2: Generazione voice pack
echo.
echo [2/4] Generazione voice pack...
set "VOICE_ARG="
if not "%VOICE%"=="" set "VOICE_ARG=--voice %VOICE%"

docker info >nul 2>&1
if not errorlevel 1 (
    echo   Generazione via Docker...
    docker compose up --build
) else (
    echo   Docker non disponibile, generazione locale...
    python voice_generator\generate_voices.py %VOICE_ARG%
)

REM Step 3: Validazione audio
echo.
echo [3/4] Validazione audio generato...
python voice_generator\validate_audio.py --input-dir output\ --report output\validation_report.txt
echo   Report salvato in output\validation_report.txt

REM Step 4: Installazione (opzionale)
if "%INSTALL%"=="true" (
    echo.
    echo [4/4] Installazione in CrewChief...
    if not "%VOICE%"=="" (
        python voice_generator\install_voicepack.py --voice "%VOICE%" --source "output\%VOICE%"
    ) else (
        for /d %%d in (output\*) do (
            echo   Installazione voce: %%~nd
            python voice_generator\install_voicepack.py --voice "%%~nd" --source "%%d"
        )
    )
) else (
    echo.
    echo [4/4] Installazione saltata - usa --install per installare
)

echo.
echo === Pipeline completata! ===
echo Output disponibile in: %CD%\output\

endlocal
