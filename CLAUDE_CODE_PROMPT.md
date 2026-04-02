# PROMPT PER CLAUDE CODE — Progetto CrewChief ITA Voice Pack

## RUOLO

Sei l'architetto e sviluppatore unico di questo progetto. Devi costruire TUTTO autonomamente: clonare repository esterne, analizzare file, creare la struttura, scrivere codice. Chiedi all'utente SOLO quando serve qualcosa che non puoi ottenere da solo (file dal suo disco locale, decisioni creative, audio di riferimento).

---

## CONTESTO DEL PROGETTO

### Obiettivo
Creare un sistema completo per generare **voice pack italiani personalizzati** per CrewChief V4, con:
1. **Voci multiple selezionabili** (maschili, femminili, diversi caratteri)
2. **Lessico italiano completamente riscritto e arricchito** con gergo motorsport autentico e varianti naturali
3. Focus specifico su **Le Mans Ultimate** (endurance, classi multiple, stint notturni, meteo)

### Cos'è CrewChief
CrewChief V4 è un'app gratuita open source (C#) che agisce come ingegnere di pista virtuale nei simulatori di guida. Comunica con il pilota tramite file audio .wav pre-registrati organizzati in cartelle tematiche. L'utente lo usa con **Le Mans Ultimate** su PC.

- Codice sorgente: `https://gitlab.com/mr_belowski/CrewChiefV4`
- Mirror GitHub: `https://github.com/mrbelowski/CrewChiefV4`

### Come funziona il sistema audio di CrewChief
- I file audio stanno in: `C:\Users\<USERNAME>\AppData\Local\CrewChiefV4\sounds\`
- Voce predefinita "Jim": `sounds\voice\`
- Voci alternative: `sounds\alt\<NomeVoce>\`
- Spotter: `sounds\voice\spotter_<NomeVoce>\`
- Radio check: `sounds\voice\radio_check_<NomeVoce>\`
- Formato: **WAV 22050Hz, 16-bit PCM mono**
- Ogni cartella scenario può avere MULTIPLI .wav → CrewChief ne sceglie uno random
- Più varianti = ingegnere più naturale

### Strumento chiave: crew-chief-autovoicepack
Repository GitHub `cktlco/crew-chief-autovoicepack`:
- Usa **Coqui XTTS v2** (supporta italiano nativo) per generare voice pack completi
- Lavora da un `phrase_inventory.csv` (cartella → frase → testo TTS)
- Genera 30.000+ file .wav per voice pack
- Supporta clonazione vocale da ~30 secondi di audio
- Richiede Docker + GPU NVIDIA
- Ha uno script `translate_phrases.py` per tradurre frasi tramite LLM

### Il pack italiano attuale
- È **incompleto**: molte frasi mancanti, fallback in inglese
- Una sola voce
- Lessico piatto, non tecnico
- Il file di configurazione per il riconoscimento vocale italiano si chiama `speech_recognition_config.txt`
- Percorso installazione CC: `C:\Program Files (x86)\Britton IT Ltd\CrewChiefV4\`
- Percorso dati utente CC: `C:\Users\<USERNAME>\AppData\Local\CrewChiefV4\`
- Il pack ITA viene copiato dentro la cartella `AppData\Local\CrewChiefV4\`

### Ambiente dell'utente
- **OS**: Windows, Docker Desktop installato
- **GPU**: NVIDIA 8GB+ VRAM
- **CrewChief**: installato con pack italiano
- **Docker**: installato e funzionante

---

## PRIMO STEP — BOOTSTRAP AUTONOMO

Quando l'utente ti dice di iniziare, fai queste operazioni **senza chiedere nulla**:

### 1. Clona le risorse esterne
```bash
# Clona la repo autovoicepack per ottenere phrase_inventory.csv e gli script
git clone https://github.com/cktlco/crew-chief-autovoicepack.git /tmp/autovoicepack

# Clona il mirror GitHub di CrewChief per analizzare la struttura e il speech_recognition_config.txt
git clone --depth 1 https://github.com/mrbelowski/CrewChiefV4.git /tmp/crewchief-source
```

### 2. Analizza i file chiave
- Leggi `/tmp/autovoicepack/phrase_inventory.csv` — capisci struttura, numero frasi, categorie
- Leggi `/tmp/autovoicepack/generate_voice_pack.py` — capisci come funziona la generazione
- Leggi `/tmp/autovoicepack/translate_phrases.py` — capisci il processo di traduzione
- Leggi `/tmp/crewchief-source/CrewChiefV4/speech_recognition_config.txt` — capisci i comandi vocali
- Esplora la struttura cartelle di `/tmp/autovoicepack/` per capire l'organizzazione

### 3. Crea la struttura della repository
Crea TUTTE le cartelle e i file necessari nella repo di lavoro.

### 4. Solo DOPO chiedi all'utente ciò che serve dal suo PC
Quando hai bisogno di file che stanno SOLO sul disco dell'utente (non reperibili online), chiediglieli con istruzioni precise. Esempio:

> "Ho bisogno di 2 cose dal tuo PC:
> 1. La struttura delle cartelle del tuo CrewChief. Apri PowerShell e lancia:
>    ```powershell
>    Get-ChildItem -Path "$env:LOCALAPPDATA\CrewChiefV4\sounds" -Recurse -Directory | ForEach-Object { $_.FullName.Replace("$env:LOCALAPPDATA\CrewChiefV4\sounds", "") } | Out-File "crewchief_structure.txt"
>    ```
>    Poi trascinami il file `crewchief_structure.txt`
>
> 2. Il file `speech_recognition_config.txt` italiano se lo hai modificato. Si trova in:
>    `C:\Users\<TUO_USER>\AppData\Local\CrewChiefV4\speech_recognition_config.txt`"

---

## MODULI DA COSTRUIRE

### MODULO 1: Lessico Italiano Arricchito (`/lexicon`)

**`phrase_inventory_ita.csv`** — Traduzione completa + arricchimento di TUTTE le frasi.

Struttura CSV (stessa dell'originale): `folder_path,subtitle,text_for_tts`

**Requisiti:**
- Traduci OGNI frase dall'originale inglese
- Per le frasi più usate (lap times, fuel, spotter calls) crea **2-4 varianti**
- Gergo motorsport italiano autentico:
  - "Stai gestendo bene le gomme" / "Ottimo degrado, continua così" / "Le coperture tengono bene"
  - "Hai pista libera, puoi spingere" / "Aria pulita davanti, dai tutto"
  - "Macchina a destra" / "Attento a destra, ti affianca"
- Frasi specifiche **Le Mans Ultimate**: stint notturni, endurance, classi multiple (Hypercar, LMDh, LMP2, LMGT3), meteo variabile
- Tono **professionale ma umano**, come ingegnere F1
- Frasi motivazionali: "Grande giro!", "Perfetto, continua così"
- Imprecazioni leggere opzionali (sweary messages): "Accidenti!", "Ma dove va questo?"

**`custom_phrases.csv`** — Frasi aggiuntive non presenti nell'originale
**`swear_phrases.csv`** — Frasi "colorite" separate
**`lmu_specific_phrases.csv`** — Specifiche Le Mans Ultimate
**`speech_recognition_ita.txt`** — Comandi vocali in italiano per il riconoscimento vocale

**IMPORTANTE**: Basa la struttura cartelle ESCLUSIVAMENTE su quella reale trovata nel `phrase_inventory.csv` originale. Non inventare percorsi.

### MODULO 2: Generazione Voci (`/voice_generator`)

1. **`generate_voices.py`** — Script principale:
   - Legge `voices_config.yaml` per le voci da generare
   - Invoca XTTS v2 con parametri corretti per ogni voce
   - Mostra progresso, supporta ripresa da interruzione
   - Salta file già generati

2. **`voices_config.yaml`** — Configurazione voci:
   ```yaml
   voices:
     Marco:
       description: "Ingegnere calmo e professionale"
       reference_audio: "./reference_audio/marco/"
       language: "it"
       speed: 1.4
       use_as_spotter: false
     Gianni:
       description: "Ingegnere aggressivo e motivante"  
       reference_audio: "./reference_audio/gianni/"
       language: "it"
       speed: 1.5
       use_as_spotter: true
     Chiara:
       description: "Voce femminile, precisa e tecnica"
       reference_audio: "./reference_audio/chiara/"
       language: "it"
       speed: 1.4
       use_as_spotter: false
   ```

3. **`install_voicepack.py`** — Installa voice pack in CrewChief:
   - Copia nella struttura corretta (`alt/`, `radio_check_`, `spotter_`)
   - Backup automatico del pack esistente
   - Verifica integrità file

4. **`enrich_lexicon.py`** — Usa API Claude (Anthropic) per:
   - Tradurre/arricchire `phrase_inventory.csv` inglese → italiano
   - Generare varianti naturali
   - Modalità interattiva per approvare frasi chiave

5. **`validate_audio.py`** — Validazione file generati:
   - Trova file vuoti, troppo corti, con artefatti
   - Report + rigenerazione selettiva

### MODULO 3: Documentazione (`/docs`)

- **`SETUP.md`** — Guida completa installazione e uso
- **`RECORDING_GUIDE.md`** — Come registrare audio di riferimento per voci custom
- **`CUSTOMIZATION.md`** — Come personalizzare lessico, voci, pronuncie

### MODULO 4: Automazione (`/scripts`)

- **`setup_environment.sh`** + **`.bat`** — Setup automatico (verifica prerequisiti, clona dipendenze, installa packages)
- **`build_all.sh`** + **`.bat`** — Pipeline completa (lessico → generazione → validazione → installazione)
- **`Dockerfile`** + **`docker-compose.yml`** — Container per la generazione

### MODULO 5: Test (`/tests`)

- **`test_lexicon.py`** — Verifica completezza CSV, corrispondenza cartelle
- **`test_audio.py`** — Verifica formato audio (22050Hz, 16-bit, mono)
- **`test_structure.py`** — Verifica struttura cartelle compatibile con CrewChief

---

## STRUTTURA REPOSITORY FINALE

```
crewchief-ita-voicepack/
├── README.md
├── LICENSE (MIT)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
│
├── lexicon/
│   ├── phrase_inventory_ita.csv
│   ├── phrase_inventory_original.csv      ← copiato da autovoicepack
│   ├── custom_phrases.csv
│   ├── swear_phrases.csv
│   ├── lmu_specific_phrases.csv
│   └── speech_recognition_ita.txt
│
├── voice_generator/
│   ├── generate_voices.py
│   ├── enrich_lexicon.py
│   ├── install_voicepack.py
│   ├── validate_audio.py
│   ├── voices_config.yaml
│   └── requirements.txt
│
├── reference_audio/
│   ├── README.md
│   ├── marco/
│   ├── gianni/
│   └── chiara/
│
├── scripts/
│   ├── setup_environment.sh
│   ├── setup_environment.bat
│   ├── build_all.sh
│   └── build_all.bat
│
├── docs/
│   ├── SETUP.md
│   ├── RECORDING_GUIDE.md
│   └── CUSTOMIZATION.md
│
├── output/                             ← gitignored, voice pack generati
│   └── .gitkeep
│
└── tests/
    ├── test_lexicon.py
    ├── test_audio.py
    └── test_structure.py
```

---

## REGOLE DI LAVORO

### Autonomia massima
- Clona, scarica, analizza tutto ciò che è disponibile online SENZA chiedere
- Crea file, cartelle, script SENZA chiedere conferma
- Committa e pusha il lavoro man mano

### Chiedi all'utente SOLO per:
- File che esistono SOLO sul suo disco locale (struttura cartelle CrewChief installato, config personalizzate)
- Decisioni creative (quali voci, quali nomi, tono preferito)
- Audio di riferimento per le voci custom (quando sarà il momento)
- Quando dai comandi PowerShell da eseguire sul suo PC, sii preciso e copia-incollabile

### Qualità del codice
- Python 3.10+ con type hints
- Docstring in italiano
- Logging strutturato
- Error handling robusto
- Config via YAML, niente path hardcoded
- README e docs in italiano

### Priorità di sviluppo
1. **Bootstrap**: clona repo esterne, analizza struttura, crea scaffolding
2. **Lessico**: `enrich_lexicon.py` + prima versione `phrase_inventory_ita.csv`
3. **Generazione**: `generate_voices.py` + integrazione con autovoicepack
4. **Installazione**: `install_voicepack.py` + validazione
5. **Documentazione e test**

### Dipendenze Python
- `coqui-tts` (XTTS v2)
- `anthropic` (per enrich_lexicon.py)
- `pyyaml`, `pandas`, `soundfile`, `librosa`, `tqdm`
