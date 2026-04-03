# Guida Installazione e Setup

## Prerequisiti

- **Windows 10/11** (testato su Windows 11 Pro)
- **Docker Desktop** installato e funzionante
- **GPU NVIDIA** con almeno 8GB VRAM (consigliato; funziona anche solo CPU ma molto piu lento)
- **CrewChief V4** installato dal sito ufficiale
- **Python 3.10+** (opzionale, per script di utilita locali)

## Installazione

### 1. Clona il repository

```bash
git clone https://github.com/TUO_USER/crewchief-ita-voicepack.git
cd crewchief-ita-voicepack
```

### 2. Setup automatico

**Windows:**
```cmd
scripts\setup_environment.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

Lo script verifichera i prerequisiti, creera un ambiente virtuale Python e installera le dipendenze.

### 3. Prepara gli audio di riferimento

Per ogni voce che vuoi generare, servono circa 20-30 secondi di audio di riferimento.
Vedi `docs/RECORDING_GUIDE.md` per i dettagli.

Copia i file audio nelle cartelle:
- `reference_audio/marco/` - per la voce Marco
- `reference_audio/gianni/` - per la voce Gianni
- `reference_audio/chiara/` - per la voce Chiara

### 4. Configura le voci (opzionale)

Modifica `voice_generator/voices_config.yaml` per personalizzare:
- Velocita TTS
- Numero varianti per frase
- Quale voce usare come spotter

### 5. Arricchisci il lessico (opzionale)

Se vuoi rigenerare o personalizzare le traduzioni italiane:

```bash
# Richiede API key Anthropic
set ANTHROPIC_API_KEY=sk-ant-...
python voice_generator/enrich_lexicon.py --input lexicon/phrase_inventory_original.csv --output lexicon/phrase_inventory_ita.csv
```

## Generazione Voice Pack

### Con Docker (consigliato)

```bash
docker compose up
```

Questo avvia la generazione nel container con tutte le dipendenze pre-installate.
I file generati vengono salvati nella cartella `output/`.

### Senza Docker (locale)

```bash
python voice_generator/generate_voices.py --voice Marco
```

Richiede `coqui-tts`, `torch`, `sox` installati localmente.

### Opzioni generazione

```bash
# Solo una voce specifica
python voice_generator/generate_voices.py --voice Marco

# Solo CPU (piu lento)
python voice_generator/generate_voices.py --cpu-only

# Rigenera tutto
python voice_generator/generate_voices.py --overwrite

# Velocita TTS personalizzata
python voice_generator/generate_voices.py --xtts-speed 1.5
```

## Installazione in CrewChief

Dopo la generazione, installa il voice pack:

```bash
python voice_generator/install_voicepack.py --voice Marco --source output/Marco
```

Lo script:
1. Crea un backup del voice pack esistente
2. Copia i file nella struttura corretta di CrewChief
3. Verifica l'integrita dei file

### Percorsi CrewChief

- **Installazione**: `C:\Program Files (x86)\Britton IT Ltd\CrewChiefV4\`
- **Dati utente**: `C:\Users\<TUO_USER>\AppData\Local\CrewChiefV4\`
- **File audio**: `...\CrewChiefV4\sounds\`
- **Voci alternative**: `...\sounds\alt\<NomeVoce>\`

### Seleziona la voce in CrewChief

1. Apri CrewChief
2. Vai su **Properties** (in alto a destra)
3. Cerca **"voice"** o **"persona"**
4. Seleziona la voce italiana dal menu a tendina
5. Riavvia CrewChief

## Validazione

Verifica che i file generati siano corretti:

```bash
python voice_generator/validate_audio.py --input-dir output/
```

Esegui i test:

```bash
python -m pytest tests/ -v
```

## Troubleshooting

### Docker non trova la GPU

Assicurati che:
1. I driver NVIDIA siano aggiornati
2. NVIDIA Container Toolkit sia installato
3. Docker Desktop abbia WSL2 backend attivo

```bash
# Verifica GPU nel container
docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu22.04 nvidia-smi
```

### Errore "XTTS model not found"

Il modello viene scaricato automaticamente al primo avvio del container Docker.
Se usi la generazione locale, scaricalo manualmente:

```bash
git lfs install
git clone --branch v2.0.3 https://huggingface.co/coqui/XTTS-v2 ~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2
```

### File audio troppo veloci/lenti

Modifica il parametro `speed` in `voices_config.yaml`:
- Valori consigliati: 1.2 - 1.7
- Piu alto = parlato piu veloce

### Memoria GPU insufficiente

- Riduci `variation_count` in `voices_config.yaml`
- Usa `--cpu-only` (molto piu lento)
- Chiudi altre applicazioni che usano la GPU

### Sox non trovato

Installa SoX per gli effetti audio:
- **Container Docker**: gia incluso
- **Windows**: scarica da https://sourceforge.net/projects/sox/
- **Linux**: `sudo apt install sox`
