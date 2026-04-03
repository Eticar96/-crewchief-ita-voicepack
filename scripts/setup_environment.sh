#!/usr/bin/env bash
# setup_environment.sh - Configurazione ambiente per CrewChief ITA Voice Pack
#
# Uso: bash scripts/setup_environment.sh
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
AUTOVOICEPACK_DIR="$PROJECT_DIR/../crew-chief-autovoicepack"
MIN_PYTHON_VERSION="3.10"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERRORE]${NC} $*"; }

echo "============================================"
echo " CrewChief ITA Voice Pack - Setup Ambiente"
echo "============================================"
echo ""

# -----------------------------------------------
# 1. Verifica prerequisiti
# -----------------------------------------------
info "Verifica prerequisiti..."

ERRORS=0

# Python 3.10+
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        info "Python $PY_VERSION trovato"
    else
        error "Python $PY_VERSION trovato, richiesto >= $MIN_PYTHON_VERSION"
        ERRORS=$((ERRORS + 1))
    fi
else
    error "Python3 non trovato. Installare Python >= $MIN_PYTHON_VERSION"
    ERRORS=$((ERRORS + 1))
fi

# Docker
if command -v docker &>/dev/null; then
    DOCKER_VERSION=$(docker --version | head -1)
    info "Docker trovato: $DOCKER_VERSION"
else
    warn "Docker non trovato. Necessario solo per esecuzione via container."
fi

# NVIDIA GPU
if command -v nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo "sconosciuta")
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -1 || echo "N/A")
    info "GPU NVIDIA trovata: $GPU_NAME ($GPU_MEM)"
else
    warn "nvidia-smi non trovato. GPU NVIDIA richiesta per generazione TTS."
fi

if [ "$ERRORS" -gt 0 ]; then
    error "$ERRORS prerequisiti mancanti. Correggere prima di continuare."
    exit 1
fi

echo ""

# -----------------------------------------------
# 2. Crea ambiente virtuale Python
# -----------------------------------------------
info "Creazione ambiente virtuale Python in $VENV_DIR ..."

if [ -d "$VENV_DIR" ]; then
    warn "Ambiente virtuale esistente trovato, verranno aggiornate le dipendenze."
else
    python3 -m venv "$VENV_DIR"
    info "Ambiente virtuale creato."
fi

# Attiva venv
source "$VENV_DIR/bin/activate"
info "Ambiente virtuale attivato."

# -----------------------------------------------
# 3. Installa dipendenze Python
# -----------------------------------------------
info "Aggiornamento pip..."
pip install --upgrade pip setuptools wheel --quiet

info "Installazione dipendenze dal requirements.txt..."
if [ -f "$PROJECT_DIR/voice_generator/requirements.txt" ]; then
    pip install -r "$PROJECT_DIR/voice_generator/requirements.txt" --quiet
    info "Dipendenze installate."
else
    error "File requirements.txt non trovato in voice_generator/"
    exit 1
fi

echo ""

# -----------------------------------------------
# 4. Clone autovoicepack (se necessario)
# -----------------------------------------------
if [ ! -d "$AUTOVOICEPACK_DIR" ]; then
    info "Clonazione crew-chief-autovoicepack come riferimento..."
    git clone https://github.com/crew-chief/crew-chief-autovoicepack.git "$AUTOVOICEPACK_DIR" 2>/dev/null || \
        warn "Impossibile clonare autovoicepack. Verificare URL e connessione."
else
    info "crew-chief-autovoicepack gia' presente in $AUTOVOICEPACK_DIR"
fi

echo ""

# -----------------------------------------------
# 5. Crea directory di output
# -----------------------------------------------
info "Creazione directory di progetto..."

mkdir -p "$PROJECT_DIR/output"
mkdir -p "$PROJECT_DIR/output/Marco"
mkdir -p "$PROJECT_DIR/output/Gianni"
mkdir -p "$PROJECT_DIR/output/Chiara"
mkdir -p "$PROJECT_DIR/reference_audio/marco"
mkdir -p "$PROJECT_DIR/reference_audio/gianni"
mkdir -p "$PROJECT_DIR/reference_audio/chiara"
mkdir -p "$PROJECT_DIR/lexicon"

info "Directory create."

echo ""

# -----------------------------------------------
# 6. Verifica audio di riferimento
# -----------------------------------------------
info "Verifica file audio di riferimento..."

REF_FOUND=0
for VOICE_DIR in "$PROJECT_DIR"/reference_audio/*/; do
    VOICE_NAME=$(basename "$VOICE_DIR")
    WAV_COUNT=$(find "$VOICE_DIR" -name "*.wav" -o -name "*.mp3" -o -name "*.flac" 2>/dev/null | wc -l)
    if [ "$WAV_COUNT" -gt 0 ]; then
        info "  $VOICE_NAME: $WAV_COUNT file audio trovati"
        REF_FOUND=$((REF_FOUND + 1))
    else
        warn "  $VOICE_NAME: nessun file audio di riferimento trovato"
        warn "    -> Aggiungere file .wav in reference_audio/$VOICE_NAME/"
    fi
done

if [ "$REF_FOUND" -eq 0 ]; then
    warn "Nessun audio di riferimento trovato."
    warn "Aggiungere file .wav (~30 secondi) nelle cartelle reference_audio/<voce>/"
fi

echo ""

# -----------------------------------------------
# Riepilogo
# -----------------------------------------------
echo "============================================"
echo " Setup completato!"
echo "============================================"
echo ""
info "Ambiente virtuale: $VENV_DIR"
info "Per attivare:      source $VENV_DIR/bin/activate"
echo ""
info "Prossimi passi:"
echo "  1. Aggiungere file audio di riferimento in reference_audio/<voce>/"
echo "  2. Verificare voices_config.yaml"
echo "  3. Eseguire: bash scripts/build_all.sh"
echo ""
echo "  Oppure con Docker:"
echo "  1. docker compose build"
echo "  2. docker compose up"
echo ""
