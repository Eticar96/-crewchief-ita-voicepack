@echo off
REM setup_environment.bat - Configurazione ambiente per CrewChief ITA Voice Pack
REM
REM Uso: scripts\setup_environment.bat
REM

setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0.."
set "VENV_DIR=%PROJECT_DIR%\.venv"
set "AUTOVOICEPACK_DIR=%PROJECT_DIR%\..\crew-chief-autovoicepack"
set "ERRORS=0"

echo ============================================
echo  CrewChief ITA Voice Pack - Setup Ambiente
echo ============================================
echo.

REM -----------------------------------------------
REM 1. Verifica prerequisiti
REM -----------------------------------------------
echo [INFO] Verifica prerequisiti...

REM Python 3.10+
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERRORE] Python non trovato. Installare Python ^>= 3.10
    set /a ERRORS+=1
) else (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VERSION=%%v
    echo [INFO] Python !PY_VERSION! trovato
    for /f "tokens=1,2 delims=." %%a in ("!PY_VERSION!") do (
        if %%a LSS 3 (
            echo [ERRORE] Python ^>= 3.10 richiesto
            set /a ERRORS+=1
        ) else if %%a EQU 3 if %%b LSS 10 (
            echo [ERRORE] Python ^>= 3.10 richiesto
            set /a ERRORS+=1
        )
    )
)

REM Docker
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Docker non trovato. Necessario solo per esecuzione via container.
) else (
    for /f "delims=" %%v in ('docker --version 2^>^&1') do echo [INFO] Docker trovato: %%v
)

REM NVIDIA GPU
nvidia-smi >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] nvidia-smi non trovato. GPU NVIDIA richiesta per generazione TTS.
) else (
    for /f "tokens=*" %%g in ('nvidia-smi --query-gpu^=name --format^=csv^,noheader 2^>nul') do (
        echo [INFO] GPU NVIDIA trovata: %%g
    )
)

if !ERRORS! GTR 0 (
    echo [ERRORE] !ERRORS! prerequisiti mancanti. Correggere prima di continuare.
    exit /b 1
)

echo.

REM -----------------------------------------------
REM 2. Crea ambiente virtuale Python
REM -----------------------------------------------
echo [INFO] Creazione ambiente virtuale Python in %VENV_DIR% ...

if exist "%VENV_DIR%" (
    echo [WARN] Ambiente virtuale esistente trovato, verranno aggiornate le dipendenze.
) else (
    python -m venv "%VENV_DIR%"
    echo [INFO] Ambiente virtuale creato.
)

REM Attiva venv
call "%VENV_DIR%\Scripts\activate.bat"
echo [INFO] Ambiente virtuale attivato.

REM -----------------------------------------------
REM 3. Installa dipendenze Python
REM -----------------------------------------------
echo [INFO] Aggiornamento pip...
pip install --upgrade pip setuptools wheel --quiet

echo [INFO] Installazione dipendenze dal requirements.txt...
if exist "%PROJECT_DIR%\voice_generator\requirements.txt" (
    pip install -r "%PROJECT_DIR%\voice_generator\requirements.txt" --quiet
    echo [INFO] Dipendenze installate.
) else (
    echo [ERRORE] File requirements.txt non trovato in voice_generator\
    exit /b 1
)

echo.

REM -----------------------------------------------
REM 4. Clone autovoicepack (se necessario)
REM -----------------------------------------------
if not exist "%AUTOVOICEPACK_DIR%" (
    echo [INFO] Clonazione crew-chief-autovoicepack come riferimento...
    git clone https://github.com/crew-chief/crew-chief-autovoicepack.git "%AUTOVOICEPACK_DIR%" 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [WARN] Impossibile clonare autovoicepack. Verificare URL e connessione.
    )
) else (
    echo [INFO] crew-chief-autovoicepack gia presente in %AUTOVOICEPACK_DIR%
)

echo.

REM -----------------------------------------------
REM 5. Crea directory di output
REM -----------------------------------------------
echo [INFO] Creazione directory di progetto...

if not exist "%PROJECT_DIR%\output\Marco" mkdir "%PROJECT_DIR%\output\Marco"
if not exist "%PROJECT_DIR%\output\Gianni" mkdir "%PROJECT_DIR%\output\Gianni"
if not exist "%PROJECT_DIR%\output\Chiara" mkdir "%PROJECT_DIR%\output\Chiara"
if not exist "%PROJECT_DIR%\reference_audio\marco" mkdir "%PROJECT_DIR%\reference_audio\marco"
if not exist "%PROJECT_DIR%\reference_audio\gianni" mkdir "%PROJECT_DIR%\reference_audio\gianni"
if not exist "%PROJECT_DIR%\reference_audio\chiara" mkdir "%PROJECT_DIR%\reference_audio\chiara"
if not exist "%PROJECT_DIR%\lexicon" mkdir "%PROJECT_DIR%\lexicon"

echo [INFO] Directory create.

echo.

REM -----------------------------------------------
REM 6. Verifica audio di riferimento
REM -----------------------------------------------
echo [INFO] Verifica file audio di riferimento...

set "REF_FOUND=0"
for /d %%d in ("%PROJECT_DIR%\reference_audio\*") do (
    set "VOICE_NAME=%%~nxd"
    set "WAV_COUNT=0"
    for %%f in ("%%d\*.wav" "%%d\*.mp3" "%%d\*.flac") do set /a WAV_COUNT+=1
    if !WAV_COUNT! GTR 0 (
        echo [INFO]   !VOICE_NAME!: !WAV_COUNT! file audio trovati
        set /a REF_FOUND+=1
    ) else (
        echo [WARN]   !VOICE_NAME!: nessun file audio di riferimento trovato
        echo [WARN]     -^> Aggiungere file .wav in reference_audio\!VOICE_NAME!\
    )
)

if !REF_FOUND! EQU 0 (
    echo [WARN] Nessun audio di riferimento trovato.
    echo [WARN] Aggiungere file .wav ^(~30 secondi^) nelle cartelle reference_audio\^<voce^>\
)

echo.

REM -----------------------------------------------
REM Riepilogo
REM -----------------------------------------------
echo ============================================
echo  Setup completato!
echo ============================================
echo.
echo [INFO] Ambiente virtuale: %VENV_DIR%
echo [INFO] Per attivare:      %VENV_DIR%\Scripts\activate.bat
echo.
echo [INFO] Prossimi passi:
echo   1. Aggiungere file audio di riferimento in reference_audio\^<voce^>\
echo   2. Verificare voices_config.yaml
echo   3. Eseguire: scripts\build_all.bat
echo.
echo   Oppure con Docker:
echo   1. docker compose build
echo   2. docker compose up
echo.

endlocal
