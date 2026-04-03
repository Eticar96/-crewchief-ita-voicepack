# CrewChief ITA Voice Pack

Sistema completo per generare **voice pack italiani personalizzati** per [CrewChief V4](https://thecrewchief.org/), con focus su **Le Mans Ultimate**.

## Caratteristiche

- **Voci multiple selezionabili**: Marco (calmo, professionale), Gianni (aggressivo, motivante), Chiara (precisa, tecnica)
- **Lessico italiano autentico**: gergo motorsport reale, varianti naturali, tono da ingegnere di pista
- **Frasi specifiche Le Mans Ultimate**: stint notturni, classi endurance (Hypercar, LMDh, LMP2, LMGT3), meteo variabile
- **30.000+ file audio** per voice pack, formato WAV 22050Hz 16-bit PCM mono
- **Generazione TTS con Coqui XTTS v2**: clonazione vocale da ~30 secondi di audio di riferimento
- **Riconoscimento vocale in italiano**: comandi vocali tradotti

## Requisiti

- Windows 10/11 con Docker Desktop
- GPU NVIDIA con 8GB+ VRAM (consigliato)
- CrewChief V4 installato
- Python 3.10+ (per script di utilita)

## Struttura del progetto

```
crewchief-ita-voicepack/
├── lexicon/                    # Lessico italiano
│   ├── phrase_inventory_ita.csv        # Traduzione completa frasi
│   ├── phrase_inventory_original.csv   # Inventario inglese originale
│   ├── custom_phrases.csv              # Frasi aggiuntive
│   ├── swear_phrases.csv               # Frasi "colorite"
│   ├── lmu_specific_phrases.csv        # Specifiche Le Mans Ultimate
│   └── speech_recognition_ita.txt      # Comandi vocali italiano
│
├── voice_generator/            # Script generazione voci
│   ├── generate_voices.py              # Generatore principale
│   ├── enrich_lexicon.py               # Arricchimento lessico via Claude API
│   ├── install_voicepack.py            # Installatore in CrewChief
│   ├── validate_audio.py               # Validazione file audio
│   ├── voices_config.yaml              # Configurazione voci
│   └── requirements.txt               # Dipendenze Python
│
├── reference_audio/            # Audio di riferimento per clonazione vocale
├── scripts/                    # Script automazione
├── docs/                       # Documentazione
├── tests/                      # Test suite
└── output/                     # Voice pack generati (gitignored)
```

## Guida rapida

### 1. Setup ambiente

```bash
# Windows
scripts\setup_environment.bat

# Linux/macOS
./scripts/setup_environment.sh
```

### 2. Arricchire il lessico (opzionale)

```bash
# Richiede API key Anthropic in .env
python voice_generator/enrich_lexicon.py --input lexicon/phrase_inventory_original.csv --output lexicon/phrase_inventory_ita.csv
```

### 3. Generare voice pack con Docker

```bash
docker compose up
```

### 4. Installare in CrewChief

```bash
python voice_generator/install_voicepack.py --voice Marco --source output/Marco
```

## Voci disponibili

| Nome | Carattere | Velocita TTS | Spotter |
|------|-----------|-------------|---------|
| Marco | Ingegnere calmo e professionale | 1.4x | No |
| Gianni | Ingegnere aggressivo e motivante | 1.5x | Si |
| Chiara | Voce femminile, precisa e tecnica | 1.4x | No |

## Crediti

- [CrewChief V4](https://thecrewchief.org/) di Jim Britton
- [crew-chief-autovoicepack](https://github.com/cktlco/crew-chief-autovoicepack) per il sistema di generazione TTS
- [Coqui XTTS v2](https://github.com/coqui-ai/TTS) per il motore text-to-speech

## Licenza

MIT - vedi [LICENSE](LICENSE)
