@echo off
REM ============================================================================
REM genera_leonardo.bat — Genera il voice pack Leonardo per CrewChief V4
REM
REM Prerequisiti:
REM   1. Metti i file audio registrati in reference_audio\leonardo\
REM      (leonardo_A01.wav, leonardo_B01.wav, leonardo_C01.wav, leonardo_D01.wav)
REM   2. Ambiente Python configurato (vedi scripts\setup_environment.bat)
REM
REM Questo script:
REM   - Cacha i speaker latents separando per blocco A/B/C/D
REM   - Genera TUTTO il voice pack Leonardo
REM   - Installa in CrewChief accanto a Marco (entrambi selezionabili)
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   GENERAZIONE VOICE PACK LEONARDO
echo ============================================================
echo.

REM Cartella root del progetto
set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

REM --- Step 0: Verifica file reference ---
echo [1/5] Verifica file reference audio...

set "REF_DIR=reference_audio\leonardo"
set "REF_COUNT=0"

for %%f in ("%REF_DIR%\*.wav" "%REF_DIR%\*.mp3" "%REF_DIR%\*.flac") do (
    set /a REF_COUNT+=1
)

if %REF_COUNT% EQU 0 (
    echo.
    echo ERRORE: Nessun file audio trovato in %REF_DIR%\
    echo.
    echo Devi mettere almeno i 4 file di registrazione:
    echo   - leonardo_A01.wav  (Blocco Tecnico)
    echo   - leonardo_B01.wav  (Blocco Spotter)
    echo   - leonardo_C01.wav  (Blocco Emotivo)
    echo   - leonardo_D01.wav  (Blocco Arrabbiato)
    echo.
    echo Vedi docs\TESTO_REGISTRAZIONE_VOCE.md per istruzioni.
    pause
    exit /b 1
)

echo   Trovati %REF_COUNT% file reference in %REF_DIR%\

REM Verifica blocchi
set "HAS_A=0"
set "HAS_B=0"
set "HAS_C=0"
set "HAS_D=0"

for %%f in ("%REF_DIR%\leonardo_A*.*") do set "HAS_A=1"
for %%f in ("%REF_DIR%\leonardo_B*.*") do set "HAS_B=1"
for %%f in ("%REF_DIR%\leonardo_C*.*") do set "HAS_C=1"
for %%f in ("%REF_DIR%\leonardo_D*.*") do set "HAS_D=1"

if %HAS_A% EQU 0 echo   ATTENZIONE: Manca Blocco A (Tecnico) - usera' embedding globale
if %HAS_B% EQU 0 echo   ATTENZIONE: Manca Blocco B (Spotter) - usera' embedding globale
if %HAS_C% EQU 0 echo   ATTENZIONE: Manca Blocco C (Emotivo) - usera' embedding globale
if %HAS_D% EQU 0 echo   ATTENZIONE: Manca Blocco D (Arrabbiato) - usera' embedding globale

echo.

REM --- Step 1: Verifica CSV corretto ---
echo [2/5] Verifica lessico...

if not exist "lexicon\phrase_inventory_ita.csv" (
    echo ERRORE: lexicon\phrase_inventory_ita.csv non trovato!
    pause
    exit /b 1
)

echo   Lessico OK
echo.

REM --- Step 2: Generazione voice pack ---
echo [3/5] Avvio generazione voice pack Leonardo...
echo   Questo processo richiede molto tempo (ore con GPU, giorni con CPU).
echo   I file vengono salvati in output\Leonardo\
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python voice_generator/generate_voices.py ^
    --config voice_generator/voices_config.yaml ^
    --phrase-inventory lexicon/phrase_inventory_ita.csv ^
    --output-dir ./output ^
    --voice Leonardo ^
    --seed 42

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRORE: Generazione fallita!
    echo Controlla i log sopra per dettagli.
    pause
    exit /b 1
)

echo.
echo   Generazione completata!
echo.

REM --- Step 3: Validazione ---
echo [4/5] Validazione audio generato...

python voice_generator/validate_audio.py ^
    --voice-dir output/Leonardo ^
    --fix

if %ERRORLEVEL% NEQ 0 (
    echo   ATTENZIONE: Alcuni file non hanno superato la validazione.
    echo   Controlla il report per dettagli.
)

echo.

REM --- Step 4: Installazione in CrewChief ---
echo [5/5] Installazione in CrewChief...
echo.

set /p INSTALL="Vuoi installare Leonardo in CrewChief ora? (S/N): "
if /i "%INSTALL%" NEQ "S" (
    echo   Installazione saltata. Puoi installarla dopo con:
    echo   python voice_generator/install_voicepack.py --voice Leonardo
    goto :done
)

python voice_generator/install_voicepack.py --voice Leonardo

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRORE: Installazione fallita!
    echo Prova con: python voice_generator/install_voicepack.py --voice Leonardo --dry-run
    pause
    exit /b 1
)

echo.
echo   Leonardo installato in CrewChief!
echo   Apri CrewChief e seleziona "Leonardo" dal menu voci.
echo   (Marco resta disponibile come voce separata)

:done
echo.
echo ============================================================
echo   COMPLETATO!
echo ============================================================
echo.
echo   Output: output\Leonardo\
echo   Reference: reference_audio\leonardo\
echo   Config: voice_generator\voices_config.yaml
echo.
pause
