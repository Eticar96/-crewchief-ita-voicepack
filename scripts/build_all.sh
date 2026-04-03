#!/bin/bash
# Pipeline completa per la generazione del voice pack italiano CrewChief
# Uso: ./scripts/build_all.sh [--install] [--voice NOME]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Colori output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

INSTALL=false
VOICE=""

# Parse argomenti
while [[ $# -gt 0 ]]; do
    case $1 in
        --install) INSTALL=true; shift ;;
        --voice) VOICE="$2"; shift 2 ;;
        *) echo "Uso: $0 [--install] [--voice NOME]"; exit 1 ;;
    esac
done

echo -e "${GREEN}=== CrewChief ITA Voice Pack - Pipeline Completa ===${NC}"
echo ""

# Step 1: Validazione lessico
echo -e "${YELLOW}[1/4] Validazione lessico...${NC}"
if [ -f "lexicon/phrase_inventory_ita.csv" ]; then
    LINES=$(wc -l < "lexicon/phrase_inventory_ita.csv")
    echo -e "  phrase_inventory_ita.csv: $LINES righe"
else
    echo -e "${RED}  ERRORE: phrase_inventory_ita.csv non trovato!${NC}"
    echo "  Esegui prima: python voice_generator/enrich_lexicon.py"
    exit 1
fi

if command -v python3 &> /dev/null; then
    python3 -m pytest tests/test_lexicon.py -v --tb=short 2>/dev/null || {
        echo -e "${YELLOW}  Warning: alcuni test lexicon falliti, continuo comunque${NC}"
    }
fi

# Step 2: Generazione voice pack
echo ""
echo -e "${YELLOW}[2/4] Generazione voice pack...${NC}"
VOICE_ARG=""
if [ -n "$VOICE" ]; then
    VOICE_ARG="--voice $VOICE"
fi

if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "  Generazione via Docker..."
    docker compose up --build
else
    echo "  Docker non disponibile, generazione locale..."
    python3 voice_generator/generate_voices.py $VOICE_ARG
fi

# Step 3: Validazione audio
echo ""
echo -e "${YELLOW}[3/4] Validazione audio generato...${NC}"
python3 voice_generator/validate_audio.py --input-dir output/ --report output/validation_report.txt
echo "  Report salvato in output/validation_report.txt"

# Step 4: Installazione (opzionale)
if [ "$INSTALL" = true ]; then
    echo ""
    echo -e "${YELLOW}[4/4] Installazione in CrewChief...${NC}"
    if [ -n "$VOICE" ]; then
        python3 voice_generator/install_voicepack.py --voice "$VOICE" --source "output/$VOICE"
    else
        for voice_dir in output/*/; do
            voice_name=$(basename "$voice_dir")
            if [ "$voice_name" != "." ]; then
                echo "  Installazione voce: $voice_name"
                python3 voice_generator/install_voicepack.py --voice "$voice_name" --source "$voice_dir"
            fi
        done
    fi
else
    echo ""
    echo -e "${YELLOW}[4/4] Installazione saltata (usa --install per installare)${NC}"
fi

echo ""
echo -e "${GREEN}=== Pipeline completata! ===${NC}"
echo "Output disponibile in: $(pwd)/output/"
