@echo off
echo ============================================
echo  TEST GENERAZIONE VOCE MARCO (20 frasi)
echo ============================================
echo.

REM Controlla che ci siano file audio di riferimento
dir /b reference_audio\marco\*.wav reference_audio\marco\*.mp3 reference_audio\marco\*.flac 2>nul
if errorlevel 1 (
    echo ERRORE: Nessun file audio trovato in reference_audio\marco\
    echo Registra 3 clip WAV con Audacity e salvali in quella cartella.
    echo Vedi le istruzioni nel README.
    pause
    exit /b 1
)

echo File audio di riferimento trovati:
dir /b reference_audio\marco\*.wav reference_audio\marco\*.mp3 reference_audio\marco\*.flac 2>nul
echo.

echo Avvio generazione test...
python voice_generator/generate_voices.py ^
    --config voice_generator/voices_config_test.yaml ^
    --phrase-inventory lexicon/phrase_inventory_test.csv ^
    --voice Marco ^
    --skip-radio-check ^
    --overwrite

echo.
echo ============================================
echo  Output in: output\test_marco\Marco\
echo ============================================
pause
