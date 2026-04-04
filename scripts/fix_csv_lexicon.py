#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per correggere il CSV del lexicon italiano CrewChief.
Categorie:
  A. Parole inglesi residue -> italiano naturale
  B. Numeri non scritti -> lettere
  C. Acronimi -> espansione pronuncia italiana
  D. Frasi troppo lunghe (>80 char) -> accorciate
  E. Frasi con inglesi nascosti
"""

import csv
import re
import sys
import os

INPUT_CSV = r"C:\Users\utente\Documents\-crewchief-ita-voicepack\lexicon\phrase_inventory_ita.csv"
OUTPUT_CSV = INPUT_CSV  # sovrascrive
REGEN_CSV = r"C:\Users\utente\Documents\-crewchief-ita-voicepack\lexicon\paths_to_regenerate_final.csv"

# Paths da NON toccare
SKIP_PATHS = ["corners", "numbers", "personalisation"]

# Contatori
counters = {"A_inglesi": 0, "B_numeri": 0, "C_acronimi": 0, "D_lunghe": 0, "E_nascosti": 0}

# ============================================================
# A. Sostituzioni esatte di frasi miste inglese/italiano
# ============================================================
EXACT_REPLACEMENTS = {
    "through cancello": "attraverso il cancello",
    "non stiamo seeing any danno alle sospensioni": "non vediamo danni alle sospensioni",
    "the trasmissione sembra a posto": "la trasmissione sembra a posto",
    "unlucky , that looks painful": "che sfortuna, brutto colpo",
    "unlucky, that looks painful": "che sfortuna, brutto colpo",
    "ignore that aerodinamica danno, e' nothing": "ignora quel danno aerodinamico, non e' niente",
    "ok, all sorted": "ok, tutto a posto",
    "incidents davanti, heads up": "incidenti davanti, attenzione",
    "non stiamo seeing any significant gomma usura": "non vediamo usura significativa delle gomme",
    "hai significant gomma usura all around": "hai usura significativa delle gomme su tutto",
    "hai cold freni all around": "hai i freni freddi su tutto",
    "cold gomme all around": "gomme fredde su tutto",
    "take it easy, hai cold gomme": "vai piano, hai le gomme fredde",
    "stiamo vedendo minor usura all around": "stiamo vedendo usura leggera su tutto",
    "non expect a blue flag": "non aspettarti bandiera blu",
    "non expect a blue": "non aspettarti bandiera blu",
    "ok niente piu' report gialle": "ok niente piu' avvisi bandiera gialla",
    "stiamo cambiando all 4 gomme and add carburante": "cambiamo tutte e quattro le gomme e aggiungiamo carburante",
    "stiamo cambiando all 4 gomme e stiamo aggiungendo carburante": "cambiamo tutte e quattro le gomme e aggiungiamo carburante",
    "stiamo cambiando all 4 gomme, no carburante": "cambiamo tutte e quattro le gomme, niente carburante",
    "stiamo cambiando all 4 gomme": "cambiamo tutte e quattro le gomme",
    "ricevuto, stiamo cambiando all 4 gomme": "ricevuto, cambiamo tutte e quattro le gomme",
    "macchina sembra a posto, no significant danno": "macchina sembra a posto, nessun danno significativo",
    "capito, siamo already expecting you": "capito, ti stavamo gia' aspettando",
    "ok, we weren't expecting you, anyway": "ok, non ti aspettavamo comunque",
    "uh, we weren't expecting you": "non ti aspettavamo",
    "siamo half-way through": "siamo a meta'",
}

# A+E. Pattern regex per parole inglesi residue in frasi italiane
ENGLISH_PATTERNS = [
    # Frasi specifiche miste
    (r"\bc'e' a macchina\b", "c'e' una macchina"),
    (r"\blui e' in lotta con noi per posizione\b", "sta lottando con noi per la posizione"),
    (r"\bminuti left\b", "minuti rimasti"),
]

# ============================================================
# B. Numeri -> lettere (solo nel contesto giusto)
# ============================================================
NUMBER_MAP = {
    "2": "due", "3": "tre", "4": "quattro", "5": "cinque",
    "6": "sei", "7": "sette", "8": "otto", "9": "nove",
    "10": "dieci", "11": "undici", "12": "dodici", "13": "tredici",
    "14": "quattordici", "15": "quindici", "16": "sedici",
    "17": "diciassette", "18": "diciotto", "19": "diciannove",
    "20": "venti", "25": "venticinque", "30": "trenta",
}

# Parole che seguono numeri e richiedono conversione
NUMBER_CONTEXTS = [
    "minut", "second", "gir", "rimast", "prima", "nello", "posizion",
    "litri", "carburant", "gomm", "stint", "pilota",
]

def numbers_to_words(text):
    """Converte numeri in lettere quando seguiti da parole note."""
    changed = False
    for num, word in sorted(NUMBER_MAP.items(), key=lambda x: -len(x[0])):
        # Pattern: numero seguito da spazio e contesto noto
        for ctx in NUMBER_CONTEXTS:
            pattern = r'\b' + re.escape(num) + r'\s+(' + ctx + r')'
            if re.search(pattern, text, re.IGNORECASE):
                new_text = re.sub(r'\b' + re.escape(num) + r'\s+(' + ctx + r')',
                                  word + r' \1', text, flags=re.IGNORECASE)
                if new_text != text:
                    text = new_text
                    changed = True

    # GT300/GT500 speciali
    if "GT300" in text:
        text = text.replace("GT300", "gitiTrecento")
        changed = True
    if "GT500" in text:
        text = text.replace("GT500", "gitiCinquecento")
        changed = True

    return text, changed


# ============================================================
# C. Acronimi
# ============================================================
ACRONYM_MAP = {
    "DTM": "ditiemme",
    "GTC": "giticì",
    "GTE": "gitiè",
    "GTP": "gitipì",
    "SVEGLIA": "sveglia",
}

def expand_acronyms(text):
    changed = False
    for acr, expanded in ACRONYM_MAP.items():
        # Match whole word, preserving surrounding text
        pattern = r'\b' + re.escape(acr) + r'\b'
        if re.search(pattern, text):
            new_text = re.sub(pattern, expanded, text)
            if new_text != text:
                text = new_text
                changed = True
    return text, changed


# ============================================================
# D. Frasi troppo lunghe (>80 char)
# ============================================================
LONG_PHRASE_REPLACEMENTS = {
    "nessuna possibilita' di tornare ai box con il cambio in quello stato, l'hai distrutto":
        "cambio distrutto, non puoi tornare ai box",
    "hai subito un po' di danno alla carrozzeria, rimani in pista, non e' troppo grave":
        "danno alla carrozzeria, rimani in pista, non e' grave",
    "le sospensioni sono completamente distrutte, non possiamo fare nulla":
        "sospensioni distrutte, non possiamo fare nulla",
    "spegnila, non c'e' nulla rimasto del cambio, abbiamo finito":
        "spegnila, cambio distrutto, abbiamo finito",
    "non c'e' nulla rimasto di questi freni, torna ai box se puoi":
        "freni distrutti, torna ai box se puoi",
    "il motore e' messo male, vai piano, vediamo se riusciamo ad arrivare al traguardo":
        "motore in brutte condizioni, vai piano per arrivare al traguardo",
    "le temperature dell'olio e dell'acqua sono entrambe alte, potresti dover rallentare un po'":
        "temperature olio e acqua alte, rallenta un po'",
    "acqua e olio sono entrambi piuttosto caldi adesso cerca di andare piano":
        "acqua e olio caldi, cerca di andare piano",
    "c'e' a macchina piu' veloce in arrivo, lui e' in lotta con noi per posizione, non expect a blue flag":
        "macchina veloce in arrivo, lotta per posizione, non aspettarti bandiera blu",
    "macchina piu' veloce in arrivo, lui e' in lotta con noi per posizione, non expect a blue":
        "macchina veloce in arrivo, lotta per posizione, non aspettarti bandiera blu",
    "macchina piu' veloce dietro, lui e' in lotta con noi per posizione, non expect a blue flag":
        "macchina veloce dietro, lotta per posizione, non aspettarti bandiera blu",
    "c'e' una macchina piu' veloce dietro, e' il leader di classe ma sta gareggiando con te per posizione, nessuna bandiera blu":
        "macchina veloce dietro, leader di classe ma gareggia con te, nessuna bandiera blu",
    "c'e' una macchina piu' veloce dietro, e' il leader di classe ma sta gareggiando con noi, non aspettarti una bandiera blu":
        "macchina veloce dietro, leader di classe ma gareggia con noi, nessuna bandiera blu",
    "c'e' una macchina piu' veloce in avvicinamento, e' il leader di classe ma sta gareggiando con noi, nessuna bandiera blu":
        "macchina veloce in avvicinamento, leader di classe ma gareggia con noi, nessuna bandiera blu",
    "c'e' una macchina piu' veloce in avvicinamento, nessuna bandiera blu, e' sullo stesso giro, e' il leader della classe":
        "macchina veloce in avvicinamento, stesso giro, leader di classe, nessuna bandiera blu",
    "c'e' una macchina piu' veloce dietro, sta gareggiando con noi per posizione, non penso che avremo una bandiera blu":
        "macchina veloce dietro, gareggia con noi per posizione, niente bandiera blu",
    "c'e' una macchina piu' veloce dietro, e' sullo stesso giro, nessuna bandiera blu":
        "macchina veloce dietro, stesso giro, nessuna bandiera blu",
    "macchina piu' lenta davanti, stiamo gareggiando con questo per posizione, non aspettarti una bandiera blu":
        "macchina lenta davanti, gareggiamo per posizione, niente bandiera blu",
    "macchina piu' lenta davanti, non avra' bandiera blu perche' sta gareggiando con noi per la posizione":
        "macchina lenta davanti, gareggia con noi per posizione, niente bandiera blu",
    "macchina piu' lenta davanti, sta gareggiando con noi per posizione, non avra' bandiera blu":
        "macchina lenta davanti, gareggia con noi per posizione, niente bandiera blu",
    "macchina lenta davanti, e' sul nostro giro, non avra' bandiera blu, sta gareggiando con noi per la posizione":
        "macchina lenta davanti, nostro giro, gareggia con noi, niente bandiera blu",
    "macchina lenta davanti, sta gareggiando con noi per la posizione, non aspettarti una bandiera blu":
        "macchina lenta davanti, gareggia con noi per posizione, niente bandiera blu",
    "macchina lenta davanti, sta gareggiando con noi per la posizione, non avra' bandiera blu":
        "macchina lenta davanti, gareggia con noi per posizione, niente bandiera blu",
    "macchina lenta davanti, si gareggia per posizione, non aspettarti una bandiera blu":
        "macchina lenta davanti, si gareggia per posizione, niente bandiera blu",
    "le gomme stanno bollendo su tutto, sono davvero calde":
        "gomme bollenti su tutto, davvero calde",
    "la carica attuale dovrebbe bastare fino alla fine della gara":
        "la carica dovrebbe bastare fino a fine gara",
    "pensiamo che arriverai alla fine con la carica attuale":
        "pensiamo che arrivi a fine gara con questa carica",
    "il lucky dog ha recuperato il suo giro, tienilo d'occhio":
        "il lucky dog ha recuperato il giro, occhio",
    "attenzione al lucky dog, sta recuperando il suo giro adesso":
        "attenzione al lucky dog, sta recuperando il giro",
    "attenzione al lucky dog, sta recuperando il suo giro":
        "attenzione al lucky dog, sta recuperando il giro",
    "livello batteria critico siamo molto bassi di energia":
        "livello batteria critico, energia molto bassa",
    "la batteria e' quasi scarica sta per finire":
        "batteria quasi scarica, sta per finire",
    "hai 10 minuti rimasti prima che dobbiamo cambiare pilota":
        "hai dieci minuti prima del cambio pilota",
    "10 minuti rimasti nello stint, dobbiamo fare il cambio pilota":
        "dieci minuti rimasti nello stint, serve cambio pilota",
    "abbiamo 2 minuti rimasti in questo stint del pilota":
        "due minuti rimasti in questo stint del pilota",
    "abbiamo bisogno di un cambio pilota tra 5 minuti":
        "serve un cambio pilota tra cinque minuti",
    "la carica attuale dovrebbe bastarti fino a meta' gara":
        "la carica dovrebbe bastarti fino a meta' gara",
    "meta' gara la potenza batteria sembra ok":
        "meta' gara, batteria ok",
    "meta' gara la batteria e' ok arriviamo alla fine":
        "meta' gara, batteria ok, arriviamo alla fine",
    "la batteria finira' tra circa dieci minuti":
        "batteria finisce tra circa dieci minuti",
    "abbiamo circa dieci minuti di carica rimasti":
        "circa dieci minuti di carica rimasti",
    "la batteria durera' ancora circa cinque minuti":
        "batteria per ancora circa cinque minuti",
    "le temperature delle gomme sono calde su tutto":
        "temperature gomme calde su tutto",
    "c'e' una macchina piu' veloce dietro, e' sullo stesso giro, nessuna bandiera blu":
        "macchina veloce dietro, stesso giro, nessuna bandiera blu",
}

def shorten_long_phrase(text):
    """Accorcia frasi >80 char. Prima prova le sostituzioni note, poi taglia."""
    if len(text) <= 80:
        return text, False

    # Prova sostituzioni note
    if text in LONG_PHRASE_REPLACEMENTS:
        return LONG_PHRASE_REPLACEMENTS[text], True

    return text, False


# ============================================================
# Processamento principale
# ============================================================
def should_skip(audio_path):
    path_lower = audio_path.lower()
    for skip in SKIP_PATHS:
        if skip in path_lower:
            return True
    return False


def apply_exact_replacements(text):
    """Applica sostituzioni esatte (case-insensitive per match, mantiene case del replacement)."""
    changed = False
    for old, new in EXACT_REPLACEMENTS.items():
        if old.lower() in text.lower():
            # Case-insensitive replacement
            pattern = re.escape(old)
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, new, text, flags=re.IGNORECASE)
                changed = True
    return text, changed


def apply_english_patterns(text):
    """Applica pattern regex per parole inglesi."""
    changed = False
    for pattern, replacement in ENGLISH_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            changed = True
    return text, changed


def fix_text(text):
    """Applica tutte le correzioni a un testo. Restituisce (testo, set_categorie)."""
    categories = set()
    original = text

    # A. Sostituzioni esatte inglese->italiano
    text, changed = apply_exact_replacements(text)
    if changed:
        categories.add("A_inglesi")

    # E. Pattern inglesi nascosti
    text, changed = apply_english_patterns(text)
    if changed:
        categories.add("E_nascosti")

    # C. Acronimi (prima dei numeri perche' GT300 contiene numeri)
    text, changed = expand_acronyms(text)
    if changed:
        categories.add("C_acronimi")

    # B. Numeri -> lettere
    text, changed = numbers_to_words(text)
    if changed:
        categories.add("B_numeri")

    # D. Frasi lunghe
    text, changed = shorten_long_phrase(text)
    if changed:
        categories.add("D_lunghe")

    return text, categories


def main():
    # Leggi CSV
    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    print(f"Lette {len(rows)} righe (incluso header)")

    header = rows[0]
    modified_rows = []  # (indice, riga_originale, riga_nuova, categorie)
    output_rows = [header]

    for i, row in enumerate(rows[1:], 1):
        if len(row) < 4:
            output_rows.append(row)
            continue

        audio_path = row[0]

        if should_skip(audio_path):
            output_rows.append(row)
            continue

        subtitle = row[2]
        tts = row[3]

        new_subtitle, cats_sub = fix_text(subtitle)
        new_tts, cats_tts = fix_text(tts)

        all_cats = cats_sub | cats_tts

        if new_subtitle != subtitle or new_tts != tts:
            new_row = list(row)
            new_row[2] = new_subtitle
            new_row[3] = new_tts
            output_rows.append(new_row)
            modified_rows.append((i, row, new_row, all_cats))
            for cat in all_cats:
                counters[cat] += 1
        else:
            output_rows.append(row)

    # Scrivi CSV corretto
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for row in output_rows:
            writer.writerow(row)

    # Scrivi CSV delle righe modificate (per rigenerazione audio)
    with open(REGEN_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["audio_path", "audio_filename", "subtitle", "text_for_tts"])
        for idx, orig, new_row, cats in modified_rows:
            writer.writerow([new_row[0], new_row[1], new_row[2], new_row[3]])

    # Report
    print(f"\n{'='*60}")
    print(f"REPORT CORREZIONI LEXICON ITALIANO")
    print(f"{'='*60}")
    print(f"Righe totali processate: {len(rows)-1}")
    print(f"Righe modificate:        {len(modified_rows)}")
    print(f"")
    print(f"Correzioni per categoria:")
    print(f"  A. Parole inglesi residue:    {counters['A_inglesi']}")
    print(f"  B. Numeri non scritti:        {counters['B_numeri']}")
    print(f"  C. Acronimi espansi:          {counters['C_acronimi']}")
    print(f"  D. Frasi lunghe accorciate:   {counters['D_lunghe']}")
    print(f"  E. Inglesi nascosti:          {counters['E_nascosti']}")
    print(f"")
    print(f"File salvati:")
    print(f"  CSV corretto:     {OUTPUT_CSV}")
    print(f"  Righe da regen:   {REGEN_CSV}")
    print(f"{'='*60}")

    # Mostra dettagli modifiche
    print(f"\nDETTAGLIO MODIFICHE:")
    print(f"{'-'*60}")
    for idx, orig, new_row, cats in modified_rows:
        cats_str = ", ".join(sorted(cats))
        print(f"\nRiga {idx} [{cats_str}]")
        print(f"  Path: {orig[0]}")
        if orig[2] != new_row[2]:
            print(f"  subtitle PRIMA: {orig[2]}")
            print(f"  subtitle DOPO:  {new_row[2]}")
        if orig[3] != new_row[3]:
            print(f"  tts PRIMA:      {orig[3]}")
            print(f"  tts DOPO:       {new_row[3]}")


if __name__ == "__main__":
    main()
