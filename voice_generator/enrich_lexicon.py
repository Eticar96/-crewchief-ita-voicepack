#!/usr/bin/env python3
"""
enrich_lexicon.py - Traduttore e arricchitore del lessico CrewChief da inglese a italiano.

Utilizza l'API Anthropic Claude per tradurre le frasi del phrase_inventory
dall'inglese all'italiano, usando terminologia autentica del motorsport italiano.
Supporta ripresa da interruzione, elaborazione a batch e modalità interattiva.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import anthropic
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Costanti e configurazione
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_BATCH_SIZE = 20
MAX_RETRIES = 3
INITIAL_BACKOFF = 2.0  # secondi

# Categorie di frasi per cui generare varianti italiane
VARIANT_CATEGORIES: dict[str, list[str]] = {
    "spotter": ["spotter", "car_left", "car_right", "three_wide", "overlap"],
    "lap_times": ["lap_time", "best_lap", "sector", "delta", "personal_best"],
    "fuel": ["fuel", "laps_of_fuel", "fuel_warning", "fuel_level"],
    "tyre": [
        "tyre", "tire", "wear", "grip", "compound",
        "soft", "medium", "hard", "intermediate", "wet",
    ],
}

SYSTEM_PROMPT = """\
Sei un traduttore specializzato in comunicazioni radio del motorsport. \
Traduci le frasi dall'inglese all'italiano seguendo queste regole:

1. TERMINOLOGIA MOTORSPORT ITALIANA AUTENTICA:
   - Usa "gomme" e NON "pneumatici"
   - "pit" resta "pit" (non tradurre)
   - "stint" resta "stint" (non tradurre)
   - "safety car" resta "safety car"
   - "box" per pit stop (come in F1 italiana)
   - "rettilineo" per "straight"
   - "curva" per "corner/turn"
   - "sorpasso" per "overtake"
   - "distacco" o "gap" per "gap"
   - "giro" per "lap"
   - "classifica" per "standings/leaderboard"
   - "bandiera" per "flag"
   - "DRS" resta "DRS"

2. TONO: professionale ma umano, come un vero ingegnere di pista F1. \
Usa il "tu" informale (come fanno gli ingegneri con i piloti).

3. SEGNAPOSTO: mantieni ESATTAMENTE i placeholder come {0}, {1}, ecc. \
Non tradurli, non spostarli, non modificarli.

4. NUMERI: nel campo text_for_tts, i numeri vanno scritti in parole italiane \
(es. "3" -> "tre", "10" -> "dieci"), MA i placeholder {0} ecc. restano invariati.

5. NATURALEZZA: le frasi devono suonare naturali in italiano, come una vera \
comunicazione radio. Non tradurre letteralmente, adatta il senso.

Rispondi SOLO con JSON valido. Nessun testo aggiuntivo.
"""


# ---------------------------------------------------------------------------
# Funzioni di utilità
# ---------------------------------------------------------------------------

def load_existing_output(output_path: Path) -> set[str]:
    """Carica le righe già tradotte dal file di output per supportare la ripresa."""
    existing: set[str] = set()
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row.get('audio_path', '')},{row.get('audio_filename', '')}"
                existing.add(key)
    return existing


def load_input(input_path: Path) -> list[dict[str, str]]:
    """Carica il file CSV di input con l'inventario delle frasi originali."""
    rows: list[dict[str, str]] = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def get_category(audio_path: str) -> str | None:
    """Determina la categoria di una frase in base al percorso audio.

    Restituisce il nome della categoria se la frase appartiene a una
    categoria per cui generare varianti, altrimenti None.
    """
    path_lower = audio_path.lower()
    for category, keywords in VARIANT_CATEGORIES.items():
        if any(kw in path_lower for kw in keywords):
            return category
    return None


def should_generate_variants(audio_path: str) -> bool:
    """Verifica se per questa frase vanno generate varianti multiple."""
    return get_category(audio_path) is not None


def build_translation_prompt(batch: list[dict[str, str]]) -> str:
    """Costruisce il prompt di traduzione per un batch di frasi.

    Restituisce un prompt formattato con le frasi da tradurre e le
    istruzioni per il formato di risposta atteso.
    """
    phrases = []
    for i, row in enumerate(batch):
        needs_variants = should_generate_variants(row["audio_path"])
        phrases.append({
            "index": i,
            "audio_path": row["audio_path"],
            "audio_filename": row["audio_filename"],
            "subtitle": row["subtitle"],
            "text_for_tts": row["text_for_tts"],
            "generate_variants": needs_variants,
        })

    prompt = f"""\
Traduci le seguenti frasi dall'inglese all'italiano per un voice pack \
di un ingegnere di pista (crew chief) per simulatori di corse.

FRASI DA TRADURRE:
{json.dumps(phrases, ensure_ascii=False, indent=2)}

FORMATO RISPOSTA - restituisci un array JSON con un oggetto per ogni frase:
{{
  "index": <indice originale>,
  "translations": [
    {{
      "audio_filename": "<nome file con numero variante>",
      "subtitle": "<sottotitolo tradotto>",
      "text_for_tts": "<testo per TTS con numeri in parole>"
    }}
  ]
}}

Per le frasi con "generate_variants": true, genera da 2 a 4 varianti \
(modi diversi di dire la stessa cosa in italiano motorsport). \
Per le varianti aggiuntive, incrementa il numero nel filename \
(es. "1.wav" -> "1.wav", "1_v2.wav", "1_v3.wav").

Per le frasi con "generate_variants": false, fornisci una sola traduzione \
mantenendo il filename originale.

Rispondi SOLO con l'array JSON, nessun altro testo o formattazione markdown.
"""
    return prompt


# ---------------------------------------------------------------------------
# Interazione con l'API Claude
# ---------------------------------------------------------------------------

def translate_batch(
    client: anthropic.Anthropic,
    batch: list[dict[str, str]],
    model: str = DEFAULT_MODEL,
) -> list[dict[str, Any]]:
    """Invia un batch di frasi a Claude per la traduzione.

    Implementa retry con backoff esponenziale in caso di errori API.
    Restituisce la lista di traduzioni parsed dal JSON di risposta.

    Raises:
        RuntimeError: se tutti i tentativi falliscono.
    """
    prompt = build_translation_prompt(batch)
    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            # Estrai il testo dalla risposta
            raw_text = response.content[0].text.strip()

            # Rimuovi eventuale wrapping markdown ```json ... ```
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            translations = json.loads(raw_text)
            return translations

        except anthropic.APIStatusError as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Errore API dopo {MAX_RETRIES} tentativi: {e}"
                ) from e
            print(
                f"  [!] Errore API (tentativo {attempt}/{MAX_RETRIES}): {e}. "
                f"Riprovo tra {backoff:.0f}s...",
                file=sys.stderr,
            )
            time.sleep(backoff)
            backoff *= 2

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Errore nel parsing della risposta dopo {MAX_RETRIES} "
                    f"tentativi: {e}"
                ) from e
            print(
                f"  [!] Risposta non valida (tentativo {attempt}/{MAX_RETRIES}): {e}. "
                f"Riprovo tra {backoff:.0f}s...",
                file=sys.stderr,
            )
            time.sleep(backoff)
            backoff *= 2

    # Non dovrebbe mai arrivarci, ma per sicurezza
    raise RuntimeError("Numero massimo di tentativi raggiunto.")


def generate_variants(
    client: anthropic.Anthropic,
    phrase: dict[str, str],
    model: str = DEFAULT_MODEL,
    num_variants: int = 3,
) -> list[dict[str, str]]:
    """Genera varianti italiane aggiuntive per una singola frase.

    Usato in modalità interattiva per rigenerare o aggiungere varianti
    a una frase specifica. Restituisce una lista di dizionari con le
    varianti generate.
    """
    prompt = f"""\
Genera {num_variants} varianti diverse in italiano per questa frase \
di un ingegnere di pista (crew chief) per simulatori di corse:

Frase originale (EN): "{phrase['subtitle']}"
TTS originale: "{phrase['text_for_tts']}"
Contesto (path): {phrase['audio_path']}

Ogni variante deve:
- Suonare naturale come una comunicazione radio F1 italiana
- Esprimere lo stesso concetto ma con parole diverse
- Mantenere eventuali placeholder {{0}}, {{1}} ecc.

Rispondi con un array JSON:
[
  {{"subtitle": "...", "text_for_tts": "..."}},
  ...
]

SOLO JSON, nessun altro testo.
"""
    backoff = INITIAL_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
            return json.loads(raw_text)

        except (anthropic.APIStatusError, json.JSONDecodeError) as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Errore nella generazione varianti dopo {MAX_RETRIES} "
                    f"tentativi: {e}"
                ) from e
            time.sleep(backoff)
            backoff *= 2

    raise RuntimeError("Numero massimo di tentativi raggiunto.")


# ---------------------------------------------------------------------------
# Salvataggio progressivo
# ---------------------------------------------------------------------------

def save_progress(
    output_path: Path,
    rows: list[dict[str, str]],
    *,
    write_header: bool = False,
) -> None:
    """Salva in modo incrementale le righe tradotte nel file di output.

    Apre il file in modalità append per supportare la ripresa da
    interruzione. Scrive l'header solo se il file è nuovo.
    """
    fieldnames = [
        "audio_path",
        "audio_filename",
        "subtitle",
        "text_for_tts",
        "original_english",
    ]
    mode = "a" if not write_header else "w"

    with open(output_path, mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Modalità interattiva
# ---------------------------------------------------------------------------

def interactive_review(
    client: anthropic.Anthropic,
    translations: list[dict[str, Any]],
    original_batch: list[dict[str, str]],
    model: str,
) -> list[dict[str, Any]]:
    """Modalità interattiva: mostra le traduzioni e chiede approvazione.

    Per ogni frase tradotta, l'utente può:
    - Premere Invio per accettare
    - Digitare 'r' per rigenerare
    - Digitare 's' per saltare
    - Digitare testo personalizzato per sovrascrivere

    Restituisce la lista di traduzioni (modificate o approvate).
    """
    reviewed: list[dict[str, Any]] = []

    for item in translations:
        idx = item["index"]
        original = original_batch[idx]

        print(f"\n{'=' * 60}")
        print(f"  Originale EN: {original['subtitle']}")
        print(f"  Path: {original['audio_path']}")
        print(f"  Traduzioni proposte:")

        for j, tr in enumerate(item["translations"]):
            print(f"    [{j + 1}] {tr['subtitle']}")
            print(f"        TTS: {tr['text_for_tts']}")

        print()
        choice = input(
            "  [Invio] accetta | [r] rigenera | [s] salta | [testo] sovrascrivi: "
        ).strip()

        if choice == "":
            reviewed.append(item)
        elif choice.lower() == "r":
            print("  Rigenerazione in corso...")
            new_variants = generate_variants(client, original, model=model)
            new_translations = []
            for k, var in enumerate(new_variants):
                base_fn = original["audio_filename"]
                fn = base_fn if k == 0 else base_fn.replace(".wav", f"_v{k + 1}.wav")
                new_translations.append({
                    "audio_filename": fn,
                    "subtitle": var["subtitle"],
                    "text_for_tts": var["text_for_tts"],
                })
            item["translations"] = new_translations
            reviewed.append(item)
        elif choice.lower() == "s":
            print("  Frase saltata.")
            continue
        else:
            # Sovrascrittura manuale
            item["translations"] = [{
                "audio_filename": original["audio_filename"],
                "subtitle": choice,
                "text_for_tts": choice,
            }]
            reviewed.append(item)

    return reviewed


# ---------------------------------------------------------------------------
# Funzione principale
# ---------------------------------------------------------------------------

def main() -> None:
    """Punto di ingresso principale dello script.

    Gestisce il parsing degli argomenti CLI, il caricamento dei dati,
    l'elaborazione a batch con l'API Claude e il salvataggio progressivo
    dei risultati tradotti.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Traduce e arricchisce il phrase_inventory di CrewChief "
            "dall'inglese all'italiano usando Claude AI."
        ),
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("lexicon/phrase_inventory_original.csv"),
        help="Percorso del file CSV di input (default: lexicon/phrase_inventory_original.csv)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("lexicon/phrase_inventory_ita.csv"),
        help="Percorso del file CSV di output (default: lexicon/phrase_inventory_ita.csv)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key Anthropic (default: variabile d'ambiente ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Numero di frasi per batch (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Modello Claude da utilizzare (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Modalità interattiva: approva ogni traduzione manualmente",
    )

    args = parser.parse_args()

    # --- Configurazione API key ---
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Errore: API key non trovata. Usa --api-key o imposta "
            "la variabile d'ambiente ANTHROPIC_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # --- Caricamento dati ---
    input_path = args.input
    output_path = args.output

    if not input_path.exists():
        print(f"Errore: file di input non trovato: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Caricamento frasi da: {input_path}")
    all_phrases = load_input(input_path)
    print(f"  Totale frasi caricate: {len(all_phrases)}")

    # --- Ripresa da interruzione ---
    already_done = load_existing_output(output_path)
    if already_done:
        print(f"  Frasi già tradotte (ripresa): {len(already_done)}")

    # Filtra le frasi già elaborate
    pending = [
        row for row in all_phrases
        if f"{row['audio_path']},{row['audio_filename']}" not in already_done
    ]
    print(f"  Frasi da tradurre: {len(pending)}")

    if not pending:
        print("Nessuna frase da tradurre. Uscita.")
        return

    # Se il file di output non esiste, scrivi l'header
    write_header = not output_path.exists() or not already_done

    if write_header:
        # Assicurati che la directory di output esista
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_progress(output_path, [], write_header=True)

    # --- Elaborazione a batch ---
    batches: list[list[dict[str, str]]] = []
    for i in range(0, len(pending), args.batch_size):
        batches.append(pending[i : i + args.batch_size])

    print(f"\nElaborazione in {len(batches)} batch da max {args.batch_size} frasi...")
    print(f"Modello: {args.model}")
    if args.interactive:
        print("Modalità: INTERATTIVA")
    print()

    total_translated = 0

    for batch_idx, batch in enumerate(tqdm(batches, desc="Batch", unit="batch")):
        tqdm.write(f"\n--- Batch {batch_idx + 1}/{len(batches)} ({len(batch)} frasi) ---")

        try:
            translations = translate_batch(client, batch, model=args.model)
        except RuntimeError as e:
            tqdm.write(f"  [ERRORE] {e}")
            tqdm.write("  Salto questo batch e continuo...")
            continue

        # Modalità interattiva
        if args.interactive:
            translations = interactive_review(
                client, translations, batch, args.model
            )

        # Prepara le righe per il salvataggio
        output_rows: list[dict[str, str]] = []
        for item in translations:
            idx = item["index"]
            original = batch[idx]

            for tr in item["translations"]:
                output_rows.append({
                    "audio_path": original["audio_path"],
                    "audio_filename": tr["audio_filename"],
                    "subtitle": tr["subtitle"],
                    "text_for_tts": tr["text_for_tts"],
                    "original_english": original["subtitle"],
                })

        # Salvataggio incrementale
        save_progress(output_path, output_rows)
        total_translated += len(output_rows)

        tqdm.write(f"  Tradotte e salvate: {len(output_rows)} righe")

    # --- Riepilogo finale ---
    print(f"\n{'=' * 60}")
    print(f"Traduzione completata!")
    print(f"  Frasi tradotte in questa sessione: {total_translated}")
    print(f"  File di output: {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
