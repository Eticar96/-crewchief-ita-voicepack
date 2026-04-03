# Guida alla Registrazione Audio di Riferimento

Per creare una voce personalizzata con XTTS v2, servono circa **20-30 secondi** di audio di riferimento di buona qualita.

## Attrezzatura

### Minimo
- Microfono del PC/laptop (qualita accettabile)
- Stanza silenziosa

### Consigliato
- Microfono USB o XLR dedicato
- Filtro anti-pop
- Ambiente trattato acusticamente (o almeno senza eco)

## Impostazioni di Registrazione

| Parametro | Valore |
|-----------|--------|
| Formato | WAV (non compresso) |
| Sample rate | 44100 Hz o superiore |
| Bit depth | 16-bit o superiore |
| Canali | Mono |

Nota: XTTS v2 accetta anche MP3 e FLAC, ma WAV offre la migliore qualita.

## Cosa Registrare

### Durata
- **Minimo**: 15 secondi di parlato effettivo
- **Ideale**: 25-30 secondi
- **Massimo**: 60 secondi (oltre non migliora)

### Contenuto consigliato

Parla in italiano con tono naturale, come un ingegnere di pista. Ecco un testo di esempio:

> "Buongiorno, sono il tuo ingegnere di pista. Oggi le condizioni sono buone,
> la temperatura dell'asfalto e intorno ai trenta gradi. Le gomme medie
> dovrebbero funzionare bene per il primo stint. Ricordati di gestire bene
> le coperture nei primi giri, poi potrai spingere. Il pit stop e previsto
> intorno al giro venti, ma vedremo come si evolve la situazione in pista.
> Concentrati sulla guida pulita e costante, i tempi verranno da soli."

### Suggerimenti per il tono

| Voce | Carattere | Suggerimento |
|------|-----------|-------------|
| Marco | Calmo, professionale | Parla in modo pacato e chiaro |
| Gianni | Aggressivo, motivante | Parla con energia e decisione |
| Chiara | Precisa, tecnica | Parla in modo chiaro e metodico |

## Come Registrare

### Con Audacity (gratuito)

1. Scarica Audacity da https://www.audacityteam.org/
2. Seleziona il microfono corretto
3. Imposta: Mono, 44100 Hz
4. Registra il testo di esempio
5. Rimuovi silenzi lunghi all'inizio e alla fine
6. Esporta come WAV

### Con il registratore di Windows

1. Apri "Registratore vocale" dal menu Start
2. Registra il testo
3. Il file viene salvato come M4A
4. Converti in WAV con: `ffmpeg -i registrazione.m4a -ar 44100 -ac 1 output.wav`

## Preparazione dei File

### Struttura cartelle

```
reference_audio/
├── marco/
│   ├── sample_01.wav
│   └── sample_02.wav    # opzionale, per piu varieta
├── gianni/
│   └── sample_01.wav
└── chiara/
    └── sample_01.wav
```

### Controlli qualita

Prima di usare i file, verifica:

- [ ] Audio pulito, senza rumore di fondo significativo
- [ ] Volume costante, senza picchi o distorsione
- [ ] Parlato naturale, non letto in modo robotico
- [ ] Nessun silenzio lungo (>2 secondi) all'interno
- [ ] Durata totale tra 15 e 60 secondi

### Pulizia con ffmpeg (opzionale)

```bash
# Normalizza volume, rimuovi rumore di fondo leggero, converti a mono 44100Hz
ffmpeg -i input.wav -af "highpass=f=80,lowpass=f=12000,loudnorm=I=-16" -ar 44100 -ac 1 output_clean.wav
```

## Suggerimenti Avanzati

- **Piu file = meglio**: XTTS v2 puo usare piu file di riferimento. 2-3 file da 10 secondi sono meglio di 1 file da 30 secondi, perche catturano piu sfumature vocali.
- **Varieta nel parlato**: includi sia frasi brevi che lunghe, domande e affermazioni.
- **Evita musica e rumori**: anche rumori di fondo leggeri possono degradare la qualita della voce clonata.
- **Testa prima di generare tutto**: genera 10-20 frasi di prova per verificare la qualita prima di lanciare la generazione completa.
