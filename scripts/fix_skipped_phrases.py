#!/usr/bin/env python3
"""
fix_skipped_phrases.py — Corregge le frasi che XTTS non riesce a generare.

Problemi: frasi troppo lunghe, caratteri corrotti, acronimi non pronunciabili.
Applica le correzioni sia al CSV principale che al file di rigenerazione.
"""

import csv
import re
import sys
from pathlib import Path

# Correzioni: vecchio testo -> nuovo testo
# Le chiavi usano il testo ESATTO presente nel CSV
FIXES = {
    # --- Encoding: è/à/ù corrotti -> apostrofo per TTS ---
    # Queste sono frasi incomplete dove CrewChief aggiunge un numero dopo
    "la temperatura della pista sta aumentando, adesso \u00e8": "la temperatura della pista aumenta, adesso e'",
    "la temperatura della pista sta scendendo, adesso \u00e8": "la temperatura della pista scende, adesso e'",
    "la temperatura della pista sta calando, adesso \u00e8": "la temperatura della pista cala, adesso e'",
    "la temperatura della pista sta salendo, adesso \u00e8": "la temperatura della pista sale, adesso e'",
    "davanti sta salendo, adesso \u00e8": "davanti sta salendo, adesso e'",
    "dietro sta salendo, adesso \u00e8": "dietro sta salendo, adesso e'",
    "il distacco davanti \u00e8 aumentato, adesso \u00e8 circa": "il distacco davanti e' aumentato, adesso e' circa",
    "sta chiudendo il distacco, adesso \u00e8": "sta chiudendo il distacco, adesso e'",
    "si sta avvicinando, il distacco adesso \u00e8": "si sta avvicinando, il distacco adesso e'",

    # --- Neutralizzazione troppo lungo ---
    "safety car in pista, siamo in regime di neutralizzazione": "safety car in pista, gara neutralizzata",
    "pace car in pista, siamo in regime di neutralizzazione": "pace car in pista, gara neutralizzata",
    "safety car in pista, bandiera gialla su tutto il circuito": "safety car in pista, gialla su tutto il circuito",

    # --- Frasi troppo lunghe (>50 char) ---
    "sta arrivando pioggia vera adesso, sembra che stia aumentando": "arriva pioggia vera, sembra in aumento",
    "met\u00e0 distanza, sembra che dovremo risparmiare un po' di carburante": "meta' distanza, dovremo risparmiare carburante",
    "met\u00e0 distanza, dovrai risparmiare un po' di carburante": "meta' distanza, dovrai risparmiare carburante",
    "ben fatto, \u00e8 stato assolutamente perfetto, ottima vittoria": "ben fatto, perfetto, ottima vittoria",
    "macchina pi\u00f9 veloce in arrivo, sono in lotta con noi per la posizione, non aspettarti bandiere blu":
        "macchina veloce in arrivo, in lotta con noi, niente bandiere blu",
    "ci sono macchine pi\u00f9 veloci in arrivo, sono in lotta per la posizione, il gruppo include il leader di classe":
        "macchine veloci in arrivo, in lotta per posizione col leader di classe",
    "macchina pi\u00f9 lenta davanti, lui \u00e8 il leader di classe per quelli":
        "macchina lenta davanti, e' il leader di classe",
    "in arrivo macchine pi\u00f9 lente, sono in lotta per la posizione":
        "in arrivo macchine lente, in lotta per posizione",
    "dobbiamo avere ritmo da qualifica ogni giro adesso, potrebbero esserci ancora possibilit\u00e0":
        "ritmo da qualifica ogni giro, ci sono ancora possibilita'",
    "ritmo da qualifica adesso, dai, puoi salvare qualcosa qui":
        "ritmo da qualifica, dai puoi salvare qualcosa",
    "abbiamo esaurito i giri consentiti, ai box questo giro":
        "giri esauriti, ai box questo giro",
    "calcola la tua perdita di tempo dal tuo prossimo giro veloce":
        "calcola la perdita tempo dal prossimo giro veloce",
    "i tuoi freni posteriori si sono surriscaldati, sono davvero caldi":
        "freni posteriori surriscaldati, sono bollenti",
    "la tua anteriore sinistra la pressione sembra molto alta":
        "anteriore sinistra la pressione sembra alta",
    "la tua anteriore sinistra la pressione sembra molto bassa":
        "anteriore sinistra la pressione sembra bassa",
    "stiamo vedendo molti bloccaggi del freno posteriore":
        "vediamo molti bloccaggi freno posteriore",
    "attenzione alla tua gomma posteriore destra, sembra piuttosto consumata":
        "attenzione alla posteriore destra, sembra consumata",
    "elleemmegitiTre pi\u00f9 lenta davanti, preparati a doppiare":
        "elleemmegititre lenta davanti, preparati a doppiare",
    "gruppo di elleemmepidue davanti, cerca spazio pulito":
        "elleemmepidue davanti, cerca spazio pulito",
    "finestra di pit stop aperta, rientri al prossimo giro":
        "finestra pit aperta, rientri al prossimo giro",
    "cambio pilota completato, stint pulito davanti a noi":
        "cambio pilota completato, stint pulito davanti",
    "dobbiamo fare un doppio stint con queste gomme, gestiscile":
        "doppio stint con queste gomme, gestiscile bene",
    "attenzione ai fari delle altre macchine, non farti abbagliare":
        "attenzione ai fari delle altre, non farti abbagliare",
    "la pista si asciuga, prepariamoci a passare alle slik":
        "pista si asciuga, prepariamoci per le slik",
    "pista mista, bagnato e asciutto, vai piano nelle zone umide":
        "pista mista bagnato e asciutto, piano nelle zone umide",
    "il radar dice pioggia fra dieci minuti, prepariamoci":
        "pioggia fra dieci minuti, prepariamoci",
    "la pioggia sta smettendo, ancora qualche giro e asciuga":
        "pioggia in calo, qualche giro e asciuga",
    "risparmia energia in questo tratto, ricarica la batteria":
        "risparmia energia qui, ricarica la batteria",
    "diploi disponibile, usalo nel rettilineo principale":
        "diploi disponibile, usalo nel rettilineo",
    "batteria bassa, vai in modalit\u00e0 ricarica per un giro":
        "batteria bassa, modalita' ricarica per un giro",
    "gestisci l'ibrido, non sprecare energia nelle curve lente":
        "gestisci l'ibrido, non sprecare nelle curve lente",
    "ottimo recupero energetico in frenata, continua cos\u00ec":
        "ottimo recupero energetico, continua cosi'",
    "non abbiamo abbastanza giri per calcolare la media carburante":
        "non abbastanza giri per la media carburante",
    "le stime carburante non sono affidabili senza tempi pit":
        "stime carburante non affidabili senza tempi pit",
    "senza cronometro pit le stime carburante sono approssimative":
        "senza tempi pit le stime carburante sono approssimative",
    "le stime di posizione non sono affidabili senza tempi pit":
        "stime posizione non affidabili senza tempi pit",
    "senza cronometro pit le stime posizione sono approssimative":
        "senza tempi pit le stime posizione sono approssimative",
    "la macchina dietro ci sta doppiando lasciala passare":
        "la macchina dietro ci doppia, lasciala passare",
    "abbiamo preso una penalita' per violazione VSC":
        "penalita' per violazione vi esse ci",

    # --- Frasi con inglese residuo ---
    "quello dietro's davvero accident-prone, fai attenzione qui":
        "quello dietro e' pericoloso, fai attenzione",
    "quello dietro's davvero accident-prone, fai attenzione":
        "quello dietro e' pericoloso, stai attento",
    "hai tagliato la pista, cancelleranno il giro e they'll cancellare the next one, too":
        "hai tagliato la pista, cancelleranno questo giro e il prossimo",

    # --- Acronimi VSC -> vi esse ci ---
    "VSC attiva rispetta il limite di velocita'": "vi esse ci attiva, rispetta il limite",
    "VSC finita si riparte": "vi esse ci finita, si riparte",
    "attenzione al limite VSC": "attenzione al limite vi esse ci",
    "resta sotto la velocita' VSC": "resta sotto la velocita' vi esse ci",
    "rallenta sei sopra il limite VSC": "rallenta, sei sopra il limite vi esse ci",
}


def apply_to_csv(csv_path, dry_run=True):
    """Applica le correzioni a un CSV."""
    rows = []
    changes = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)

        for row in reader:
            if len(row) >= 4:
                old_tts = row[3]
                new_tts = FIXES.get(old_tts, old_tts)

                # Prova anche con normalizzazione unicode
                if new_tts == old_tts:
                    for old, new in FIXES.items():
                        if old_tts.strip() == old.strip():
                            new_tts = new
                            break

                if new_tts != old_tts:
                    changes += 1
                    if not dry_run:
                        row[3] = new_tts
                        # Aggiorna anche subtitle se uguale al tts
                        if len(row) >= 3 and row[2] == old_tts:
                            row[2] = new_tts

            rows.append(row)

    if not dry_run and changes > 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    return changes


def main():
    dry_run = "--apply" not in sys.argv
    base = Path(__file__).parent.parent

    csv_files = [
        base / "lexicon" / "phrase_inventory_ita.csv",
        base / "lexicon" / "paths_to_regenerate_all.csv",
        base / "lexicon" / "paths_to_regenerate_mixed.csv",
        base / "lexicon" / "lmu_specific_phrases.csv",
        base / "lexicon" / "phrases_to_regenerate_leonardo.csv",
    ]

    mode = "APPLICAZIONE" if not dry_run else "DRY-RUN"
    print(f"\n  CORREZIONE FRASI PROBLEMATICHE PER XTTS — {mode}\n")

    total = 0
    for csv_path in csv_files:
        if csv_path.exists():
            n = apply_to_csv(str(csv_path), dry_run=dry_run)
            if n > 0:
                print(f"  {csv_path.name}: {n} correzioni")
            total += n

    print(f"\n  TOTALE: {total} frasi corrette\n")

    if dry_run:
        print("  Per applicare: python scripts/fix_skipped_phrases.py --apply\n")


if __name__ == "__main__":
    main()
