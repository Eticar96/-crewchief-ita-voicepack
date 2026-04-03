# Guida alla Personalizzazione

## Modificare le Frasi

### Phrase Inventory principale

Il file `lexicon/phrase_inventory_ita.csv` contiene tutte le frasi tradotte in italiano.

Formato CSV:
```
audio_path,audio_filename,subtitle,text_for_tts
\voice\fuel\low_fuel,1.wav,carburante basso,carburante basso
```

- `audio_path`: percorso cartella (deve corrispondere alla struttura CrewChief)
- `audio_filename`: nome file WAV
- `subtitle`: testo visualizzato (sottotitolo in-game)
- `text_for_tts`: testo letto dal TTS (puo differire per pronuncia)

### Aggiungere varianti

Per rendere l'ingegnere piu naturale, aggiungi varianti nella stessa cartella:

```csv
\voice\fuel\low_fuel,1.wav,carburante basso,carburante basso
\voice\fuel\low_fuel,2.wav,attenzione al carburante,attenzione al carburante
\voice\fuel\low_fuel,3.wav,stiamo finendo la benzina,stiamo finendo la benzina
```

CrewChief sceglie casualmente tra le varianti disponibili.

### File supplementari

- `lexicon/custom_phrases.csv` - frasi aggiuntive personalizzate
- `lexicon/swear_phrases.csv` - frasi "colorite" (attivabili in CrewChief)
- `lexicon/lmu_specific_phrases.csv` - frasi specifiche Le Mans Ultimate

## Creare una Nuova Voce

### 1. Prepara l'audio di riferimento

Crea una cartella in `reference_audio/` con il nome della voce:

```
reference_audio/
└── alessandro/
    ├── sample_01.wav
    └── sample_02.wav
```

Vedi `docs/RECORDING_GUIDE.md` per i requisiti audio.

### 2. Aggiungi la configurazione

In `voice_generator/voices_config.yaml`:

```yaml
voices:
  Alessandro:
    description: "Ingegnere esperto, voce profonda"
    reference_audio: "./reference_audio/alessandro/"
    language: "it"
    speed: 1.4
    use_as_spotter: false
    variation_count: 2
```

### 3. Genera il voice pack

```bash
python voice_generator/generate_voices.py --voice Alessandro
```

### Parametri voce

| Parametro | Descrizione | Valori |
|-----------|-------------|--------|
| `speed` | Velocita del parlato | 1.0-2.0 (consigliato 1.2-1.7) |
| `use_as_spotter` | Usa come voce spotter | true/false |
| `variation_count` | Varianti per frase | 0-4 (consigliato 2) |
| `language` | Lingua TTS | "it" per italiano |

## Effetti Audio

Gli effetti audio vengono applicati per simulare una comunicazione radio da motorsport.

### Configurazione in voices_config.yaml

```yaml
generation:
  audio_effects:
    enabled: true
    equalizer:
      - { freq: 100, q: 0.5, gain: -12 }   # Taglia bassi
      - { freq: 3000, q: 0.5, gain: 6 }     # Enfatizza medi
      - { freq: 6000, q: 0.5, gain: 4 }     # Enfatizza alti
    overdrive: { gain: 7, colour: 12 }       # Leggera distorsione radio
    normalize: -1                             # Normalizzazione volume
```

### Disabilitare gli effetti

Per audio "pulito" senza effetto radio, imposta `enabled: false` nella sezione `audio_effects`.

### Personalizzare l'EQ

- **Piu effetto radio**: aumenta il taglio dei bassi (gain piu negativo su 100-300 Hz)
- **Voce piu calda**: riduci il boost sugli alti (gain piu basso su 6000-10000 Hz)
- **Piu distorsione**: aumenta `overdrive.gain` (max consigliato: 15)

## Comandi Vocali

Il file `lexicon/speech_recognition_ita.txt` contiene i comandi vocali in italiano per il riconoscimento vocale di CrewChief.

### Formato

```
COMANDO = frase1:frase2:frase3
```

Le frasi alternative sono separate da `:` (due punti). CrewChief riconosce qualsiasi delle varianti.

### Aggiungere comandi personalizzati

```
# Esempio: modo personalizzato di chiedere il carburante
HOWS_MY_FUEL = quanta benzina ho:come va il carburante:livello benzina
```

### Installare i comandi vocali

Copia `speech_recognition_ita.txt` in:
```
C:\Users\<TUO_USER>\AppData\Local\CrewChiefV4\speech_recognition_config.txt
```

**Nota**: il file deve chiamarsi `speech_recognition_config.txt` (non `_ita`).

## Frasi Le Mans Ultimate

Le frasi in `lexicon/lmu_specific_phrases.csv` coprono scenari specifici dell'endurance:

- **Classi**: Hypercar, LMDh, LMP2, LMGT3
- **Stint notturni**: visibilita, fari, alba
- **Meteo**: transizioni pioggia/asciutto, pista bagnata
- **Gestione energia**: deploy ibrido, batteria, recupero

Per aggiungere nuove frasi LMU, usa le cartelle `\voice\lmu\`:
```csv
\voice\lmu\class_info,9.wav,la hypercar davanti sta rallentando,la ipercar davanti sta rallentando
```

## Rigenerare il Lessico

Per rigenerare le traduzioni italiane da zero usando Claude:

```bash
# Richiede ANTHROPIC_API_KEY
python voice_generator/enrich_lexicon.py \
    --input lexicon/phrase_inventory_original.csv \
    --output lexicon/phrase_inventory_ita.csv \
    --batch-size 20
```

### Modalita interattiva

Per approvare manualmente le traduzioni chiave:

```bash
python voice_generator/enrich_lexicon.py \
    --input lexicon/phrase_inventory_original.csv \
    --output lexicon/phrase_inventory_ita.csv \
    --interactive
```

In modalita interattiva, per ogni batch puoi:
- Accettare la traduzione
- Rigenerare con una nuova traduzione
- Modificare manualmente
- Saltare
