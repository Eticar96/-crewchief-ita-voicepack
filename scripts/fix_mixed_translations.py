#!/usr/bin/env python3
"""
fix_mixed_translations.py — Corregge le frasi miste ITA/ENG nel lexicon.

Legge phrase_inventory_ita.csv, applica le correzioni alle colonne subtitle
e text_for_tts, e salva il risultato. Genera anche la lista dei file WAV
da rigenerare.

Uso:
    python scripts/fix_mixed_translations.py                    # dry-run
    python scripts/fix_mixed_translations.py --apply            # applica
    python scripts/fix_mixed_translations.py --apply --verbose  # dettagli
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path

# =========================================================================
# Mappa delle sostituzioni frase-per-frase (pattern -> sostituzione)
# L'ordine conta: le sostituzioni più specifiche vanno prima
# =========================================================================

# Sostituzioni esatte di frasi intere o semi-intere
PHRASE_REPLACEMENTS = [
    # --- Frasi completamente rotte (traduzione parziale grave) ---
    ("light pioggia now, sembra che e' getting better", "pioggia leggera ora, sembra che stia migliorando"),
    ("abbiamo light pioggia qui, e' clearing up", "abbiamo pioggia leggera qui, si sta schiarendo"),
    ("abbiamo light pioggia qui, getting harder", "abbiamo pioggia leggera qui, sta aumentando"),
    ("siamo getting proper pioggia now, sembra che e' getting harder", "sta arrivando pioggia vera adesso, sembra che stia aumentando"),
    ("stiamo vedendo some pioggia", "stiamo vedendo un po' di pioggia"),
    ("half-carburante, hai used half your carburante", "metà carburante, hai usato metà del tuo carburante"),
    ("hai cut the track, they're gonna cancellare the giro", "hai tagliato la pista, cancelleranno il giro"),
    ("qualifying pace now, come on, puoi salvage something qui", "ritmo da qualifica adesso, dai, puoi salvare qualcosa qui"),
    ("we need quali-pace every giro now, , there might ancora be chances qui", "dobbiamo avere ritmo da qualifica ogni giro adesso, potrebbero esserci ancora possibilità"),
    ("non wait too long, find that distacco", "non aspettare troppo, trova quel distacco"),
    ("calculate your time loss da your next flying giro", "calcola la tua perdita di tempo dal tuo prossimo giro veloce"),
    ("lookout per your right gomma posteriore, , e' looking piuttosto worn", "attenzione alla tua gomma posteriore destra, sembra piuttosto consumata"),
    ("c'e' some faster cars in arrivo, they're in lotta per posizione, the group includes the leader di classe",
     "ci sono macchine più veloci in arrivo, sono in lotta per la posizione, il gruppo include il leader di classe"),
    ("macchina piu' lenta davanti, lui e' the leader di classe per these guys", "macchina più lenta davanti, lui è il leader di classe per quelli"),
    ("in arrivo some slower cars, these guys are in lotta per posizione", "in arrivo macchine più lente, sono in lotta per la posizione"),
    ("the guy dietro doesn't gara molto clean", "quello dietro non gareggia molto pulito"),
    ("stiamo vedendo lots of rear brake locking", "stiamo vedendo molti bloccaggi del freno posteriore"),
    ("5 minutes of carburante remaining, 5 minutes", "5 minuti di carburante rimasti, 5 minuti"),
    ("hai 2 minutes of carburante remaining", "hai 2 minuti di carburante rimasti"),
    ("2 giri of carburante remaining", "2 giri di carburante rimasti"),
    ("meta' distanza, looking buono per carburante", "metà distanza, sembra buono per il carburante"),
    ("meta' distanza, sembra che gonna need to save some carburante", "metà distanza, sembra che dovremo risparmiare un po' di carburante"),
    ("meta' distanza, dovrai save some carburante", "metà distanza, dovrai risparmiare un po' di carburante"),
    ("be careful, abbiamo a full course caution", "stai attento, abbiamo una neutralizzazione totale"),
    ("some minor aerodinamica danno", "danno aerodinamico minore"),
    ("stiamo vedendo some minor aerodinamica danno", "stiamo vedendo un danno aerodinamico minore"),
    ("stiamo vedendo some danno minore alle sospensioni", "stiamo vedendo un danno minore alle sospensioni"),
    ("hai some minor sospensione danno there", "hai un danno minore alle sospensioni"),
    ("hai some serious sospensione danno there", "hai un danno serio alle sospensioni"),
    ("your sospensione's looking piuttosto brutto", "la tua sospensione sembra messa piuttosto male"),
    ("your sospensione sembra a posto", "la tua sospensione sembra a posto"),
    ("pilota change, pit now", "cambio pilota, ai box adesso"),
    ("ok, siamo all buono now", "ok, siamo a posto adesso"),
    ("ok, siamo now recording pace notes", "ok, stiamo registrando le note di passo"),
    ("siamo quickest right now", "siamo i più veloci adesso"),
    ("puoi now switch to options", "puoi adesso passare alle opzioni"),
    ("puoi now switch to primes", "puoi adesso passare alle prime"),
    ("we've used our giro allowance, pit this giro", "abbiamo esaurito i giri consentiti, ai box questo giro"),
    ("ok, let's find a buono rhythm, make some places", "ok, troviamo un buon ritmo, guadagniamo posizioni"),
    ("buono pass, now keep pushing", "bel sorpasso, adesso continua a spingere"),
    ("giri remaining", "giri rimasti"),
    ("be ready, stiamo andando green", "preparati, si riparte"),
    ("heads up, stiamo andando green", "attenzione, si riparte"),
    ("safety macchina out, siamo under caution", "safety car in pista, siamo in regime di neutralizzazione"),
    ("safety macchina's out, full course yellow", "safety car in pista, bandiera gialla su tutto il circuito"),
    ("pace macchina's out, siamo under caution", "pace car in pista, siamo in regime di neutralizzazione"),
    ("ben fatto, , that was absolutely perfect, ottimo win", "ben fatto, è stato assolutamente perfetto, ottima vittoria"),
    ("fucking awesome result, , well done", "risultato pazzesco, ben fatto"),
    ("ok, e' over, ben fatto, , buono finish", "ok, è finita, ben fatto, buon risultato"),
    ("ok, the finish, ben fatto", "ok, è il traguardo, ben fatto"),
    ("well done, , buono finish", "ben fatto, buon risultato"),
    ("c'e' the finish, buono drive", "ecco il traguardo, bella guida"),
    ("e c'e' the finish, buono result, , ben fatto", "ed ecco il traguardo, buon risultato, ben fatto"),
    ("ok the end, buono finish, , ben fatto", "ok è la fine, buon risultato, ben fatto"),
    ("preparati, , e' hammer time", "preparati, è il momento di spingere"),
    ("your il piu' veloce giro today", "il tuo giro più veloce oggi"),
    ("buono giro, your il piu' veloce finora", "buon giro, il tuo più veloce finora"),
    ("buono giro, your il piu' veloce today", "buon giro, il tuo più veloce oggi"),
    ("one more giro, p1", "ancora un giro, primo"),
    ("two giri left, p1", "due giri rimasti, primo"),
    ("two giri left", "due giri rimasti"),
    ("two giri remaining", "due giri rimasti"),
    ("ricevuto, no formation giro", "ricevuto, niente giro di formazione"),
    ("capito, manual formation giro", "capito, giro di formazione manuale"),
    ("ottimo drive, a podium", "ottima guida, un podio"),
    ("a win, ottimo job, ben fatto", "una vittoria, ottimo lavoro, ben fatto"),
    ("The Left-Right before the Mountain", "La sinistra-destra prima della Montagna"),
    ("The Right-Hander before Charlies", "La destra prima di Charlies"),
    ("The Right-Left dopo Mansfield", "La destra-sinistra dopo Mansfield"),
    ("white flag, last giro", "bandiera bianca, ultimo giro"),
    ("nice giro", "bel giro"),
    ("slow macchina davanti, stay alta", "macchina lenta davanti, resta alta"),

    # Frasi miste gravi rimanenti
    ("macchina piu' veloce in arrivo, they're in lotta con noi per posizione - non expect e blue flag",
     "macchina più veloce in arrivo, sono in lotta con noi per la posizione, non aspettarti bandiere blu"),
    # Frasi incomplete — CrewChief aggiunge un numero dopo "is now"
    # Gestisce sia originali che fix errati precedenti
    ("davanti sta salendo, è adesso", "davanti sta salendo, adesso è"),
    ("dietro sta salendo, è adesso", "dietro sta salendo, adesso è"),
    ("il distacco davanti è aumentato, è adesso circa", "il distacco davanti è aumentato, adesso è circa"),
    ("sta chiudendo il distacco, è adesso", "sta chiudendo il distacco, adesso è"),
    ("si sta avvicinando, il distacco è adesso", "si sta avvicinando, il distacco adesso è"),
    ("si sta avvicinando, il distacco adesso è", "si sta avvicinando, il distacco adesso è"),
    ("davanti is sta salendo, e' now", "davanti sta salendo, adesso è"),
    ("dietro is sta salendo, e' now", "dietro sta salendo, adesso è"),
    ("il distacco davanti has increased, e' now about", "il distacco davanti è aumentato, adesso è circa"),
    ("is closing il distacco, e' now", "sta chiudendo il distacco, adesso è"),
    ("is getting closer, il distacco's now", "si sta avvicinando, il distacco adesso è"),
    ("il tuo rear freni have surriscaldati, they're davvero hot", "i tuoi freni posteriori si sono surriscaldati, sono davvero caldi"),
    ("gonna need new gomme all around", "serviranno gomme nuove su tutte e quattro"),

    # Temperature — frasi incomplete, CrewChief aggiunge un numero dopo
    # "it's now [32 degrees]" -> "adesso è [32 gradi]"
    # Gestisce sia il testo originale "e' now" che il fix errato "è adesso"
    ("la temperatura della pista sta scendendo, è adesso", "la temperatura della pista sta scendendo, adesso è"),
    ("la temperatura della pista sta calando, è adesso", "la temperatura della pista sta calando, adesso è"),
    ("la temperatura della pista sta salendo, è adesso", "la temperatura della pista sta salendo, adesso è"),
    ("la temperatura della pista sta aumentando, è adesso", "la temperatura della pista sta aumentando, adesso è"),
    ("la temperatura della pista sta scendendo, e' now", "la temperatura della pista sta scendendo, adesso è"),
    ("la temperatura della pista sta calando, e' now", "la temperatura della pista sta calando, adesso è"),
    ("la temperatura della pista sta salendo, e' now", "la temperatura della pista sta salendo, adesso è"),
    ("la temperatura della pista sta aumentando, e' now", "la temperatura della pista sta aumentando, adesso è"),

    # --- Sostituzioni di pattern ricorrenti ---
    # Bandiere
    ("green flag,", "bandiera verde,"),
    ("yellow flag,", "bandiera gialla,"),
    ("blue flag,", "bandiera blu,"),
    ("white flag,", "bandiera bianca,"),

    # Caution (contesto USA)
    ("caution totale stai attento", "neutralizzazione totale, stai attento"),
    ("caution totale attenzione", "neutralizzazione totale, attenzione"),
    ("caution totale", "neutralizzazione totale"),
    ("siamo under caution, pits closed", "siamo in regime di neutralizzazione, box chiusi"),
    ("under caution", "in regime di neutralizzazione"),

    # Start
    ("ok, rolling start", "ok, partenza lanciata"),
    ("ok, standing start", "ok, partenza da fermo"),
    ("rolling start", "partenza lanciata"),
    ("standing start", "partenza da fermo"),

    # Job -> lavoro
    ("ottimo job", "ottimo lavoro"),
    ("buono job", "bravo"),

    # Well done
    ("nice start, , well done", "bella partenza, ben fatto"),
    ("well done", "ben fatto"),

    # Small/big nel codriver
    ("big salto", "grande salto"),
    ("small dosso", "piccolo dosso"),

    # Slow car
    ("slow macchina davanti", "macchina lenta davanti"),
    ("slower class macchina davanti", "macchina di classe più lenta davanti"),
    ("slower macchina", "macchina più lenta"),
]

# Sostituzioni singole di parole (applicate DOPO le frasi)
WORD_REPLACEMENTS = [
    # Parole che non dovrebbero MAI restare in inglese nel text_for_tts
    (r'\bbuono start\b', 'buona partenza'),
    (r'\bbuono finish\b', 'buon risultato'),
    (r'\bbuono drive\b', 'bella guida'),
    (r'\bbuono result\b', 'buon risultato'),
    (r'\bbuono pass\b', 'bel sorpasso'),
    (r'\bnice start\b', 'bella partenza'),
    (r'\bnice finish\b', 'bel risultato'),
    (r'\bgood start\b', 'buona partenza'),
    (r'\bgood finish\b', 'buon risultato'),
    (r'\bgreat start\b', 'grande partenza'),
    (r'\byour left front\b', 'la tua anteriore sinistra'),
    (r'\byour right front\b', 'la tua anteriore destra'),
    (r'\byour left rear\b', 'la tua posteriore sinistra'),
    (r'\byour right rear\b', 'la tua posteriore destra'),
    (r'\byour left gomma anteriore\b', 'la tua gomma anteriore sinistra'),
    (r'\byour right gomma anteriore\b', 'la tua gomma anteriore destra'),
    (r'\byour left gomma posteriore\b', 'la tua gomma posteriore sinistra'),
    (r'\byour right gomma posteriore\b', 'la tua gomma posteriore destra'),
    (r'\bleft gomma anteriore\b', 'gomma anteriore sinistra'),
    (r'\bright gomma anteriore\b', 'gomma anteriore destra'),
    (r'\bleft gomma posteriore\b', 'gomma posteriore sinistra'),
    (r'\bright gomma posteriore\b', 'gomma posteriore destra'),
    (r'\bleft front\b', 'anteriore sinistra'),
    (r'\bright front\b', 'anteriore destra'),
    (r'\bleft rear\b', 'posteriore sinistra'),
    (r'\bright rear\b', 'posteriore destra'),
    (r'\bhai danneggiato your\b', 'hai danneggiato la tua'),
    (r'\bstai cuocendo le tue\b', 'stai cuocendo le tue'),  # OK come è
    (r'\byour\b', 'il tuo'),
    (r'\bthe guy dietro\b', 'quello dietro'),
    (r'\bpulling away da the guy dietro\b', 'ti stai allontanando da quello dietro'),
    (r'\bthe guy\b', 'quello'),
    (r'\benough\b', 'abbastanza'),
    (r'\bformation giro\b', 'giro di formazione'),
    (r'\bminutes\b', 'minuti'),
    (r'\bremaining\b', 'rimasti'),
    (r'\bpodium\b', 'podio'),
    (r'\btoday\b', 'oggi'),
]


def apply_fixes(text: str) -> str:
    """Applica tutte le correzioni a una stringa di testo."""
    result = text

    # Prima le sostituzioni di frasi intere/parziali (case-insensitive)
    for old, new in PHRASE_REPLACEMENTS:
        if old.lower() in result.lower():
            # Sostituzione case-insensitive preservando il case originale dove possibile
            result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)

    # Poi le sostituzioni regex di parole
    for pattern, replacement in WORD_REPLACEMENTS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def process_csv(csv_path: str, apply: bool = False, verbose: bool = False):
    """Processa un file CSV e trova/corregge le traduzioni miste."""
    rows = []
    changes = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)

        for row_num, row in enumerate(reader, start=2):
            if len(row) < 4:
                rows.append(row)
                continue

            audio_path = row[0]
            audio_filename = row[1]
            subtitle_orig = row[2]
            tts_orig = row[3]

            subtitle_fixed = apply_fixes(subtitle_orig)
            tts_fixed = apply_fixes(tts_orig)

            changed = False
            if subtitle_fixed != subtitle_orig or tts_fixed != tts_orig:
                changed = True
                changes.append({
                    "row": row_num,
                    "path": audio_path,
                    "filename": audio_filename,
                    "subtitle_old": subtitle_orig,
                    "subtitle_new": subtitle_fixed,
                    "tts_old": tts_orig,
                    "tts_new": tts_fixed,
                })

            if apply and changed:
                row[2] = subtitle_fixed
                row[3] = tts_fixed

            rows.append(row)

    if apply and changes:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    return changes


def main():
    parser = argparse.ArgumentParser(description="Corregge frasi miste ITA/ENG nel lexicon")
    parser.add_argument("--apply", action="store_true", help="Applica le correzioni (default: dry-run)")
    parser.add_argument("--verbose", action="store_true", help="Mostra dettagli di ogni correzione")
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    csv_files = [
        base / "lexicon" / "phrase_inventory_ita.csv",
        base / "lexicon" / "lmu_specific_phrases.csv",
        base / "lexicon" / "custom_phrases.csv",
        base / "lexicon" / "swear_phrases.csv",
        base / "lexicon" / "phrase_inventory_missing.csv",
    ]

    all_changes = []
    mode = "APPLICAZIONE" if args.apply else "DRY-RUN"
    print(f"\n{'='*60}")
    print(f"  CORREZIONE TRADUZIONI MISTE ITA/ENG — {mode}")
    print(f"{'='*60}\n")

    for csv_path in csv_files:
        if not csv_path.exists():
            print(f"  SKIP: {csv_path.name} non trovato")
            continue

        changes = process_csv(str(csv_path), apply=args.apply, verbose=args.verbose)
        print(f"  {csv_path.name}: {len(changes)} correzioni")

        if args.verbose:
            for c in changes:
                print(f"    riga {c['row']}: {c['path']}/{c['filename']}")
                if c['tts_old'] != c['tts_new']:
                    print(f"      TTS: \"{c['tts_old']}\"")
                    print(f"        -> \"{c['tts_new']}\"")

        all_changes.extend(changes)

    print(f"\n  TOTALE: {len(all_changes)} frasi corrette\n")

    # Genera lista file WAV da rigenerare
    regen_path = base / "lexicon" / "paths_to_regenerate_mixed.csv"
    with open(regen_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["audio_path", "audio_filename", "subtitle", "text_for_tts"])
        for c in all_changes:
            writer.writerow([c["path"], c["filename"], c["subtitle_new"], c["tts_new"]])

    print(f"  Lista file da rigenerare: {regen_path}")
    print(f"  File da rigenerare: {len(all_changes)}\n")

    if not args.apply:
        print("  Per applicare le correzioni: python scripts/fix_mixed_translations.py --apply")
        print()


if __name__ == "__main__":
    main()
