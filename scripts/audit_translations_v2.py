#!/usr/bin/env python3
"""
Audit script v2 for Italian voice pack translations.
Smarter detection: focuses on mixed ITA/ENG phrases and clearly untranslated text.
Excludes Italian words that happen to look like English (e.g., "fine", "temperature", "come").
"""

import csv
import re
import sys
from collections import defaultdict

# Italian words that look like English words - NEVER flag these
ITALIAN_WORDS_LIKE_ENGLISH = {
    "fine",       # = end
    "temperature",# = temperatures (plural)
    "come",       # = how/like
    "per",        # = for
    "via",        # = away/street
    "ore",        # = hours
    "persona",    # = person
    "sole",       # = sun
    "mare",       # = sea
    "note",       # = notes
    "base",       # = base
    "auto",       # = car
    "radio",      # = radio
    "forma",      # = form/shape
    "piano",      # = floor/plan/slowly
    "largo",      # = wide
    "volume",     # = volume
    "meta",       # = half/destination
    "vista",      # = view
    "forte",      # = strong
    "notte",      # = night
    "luce",       # = light
    "male",       # = bad/pain
    "parte",      # = part
    "porta",      # = door/carries
    "case",       # = houses
    "sale",       # = salt/goes up
    "era",        # = was/era
    "fare",       # = to do
    "dare",       # = to give
    "dire",       # = to say
    "sole",       # = sun
    "pace",       # = peace (but "pace car" is a real issue if it should be "safety car")
    "continue",   # = you continue (imperative)
    "ancora",     # = still/again
    "solo",       # = alone/only
    "quasi",      # = almost
    "fatto",      # = done/fact
    "stato",      # = been/state
    "passa",      # = passes
    "gara",       # = race
    "ora",        # = now/hour
    "data",       # = date
    "vice",       # = deputy
    "mobile",     # = mobile
    "tale",       # = such
    "reale",      # = real/royal
    "locale",     # = local
    "finale",     # = final
    "media",      # = average/media
    "regime",     # = regime
    "test",       # = test (commonly used)
    "corner",     # ok in corner names
    "pass",       # could be Italian context
    "report",     # borderline - used in Italian racing
    "soft",       # mescola soft - acceptable in racing
    "hard",       # mescola hard - acceptable in racing
    "medium",     # mescola medium - acceptable
    "formula",    # = formula
    "podio",      # Italian for podium
    "video",      # = video
    "numero",     # = number
    "terra",      # = earth
    "sera",       # = evening
    "bene",       # = well
    "dopo",       # = after
    "prima",      # = before/first
    "contro",     # = against
    "dentro",     # = inside
    "fuori",      # = outside
    "anche",      # = also
    "ogni",       # = every
    "questo",     # = this
    "quello",     # = that
    "molto",      # = very
    "troppo",     # = too much
    "sempre",     # = always
    "cosi",       # = so/like this
    "pure",       # = also/pure
    "meno",       # = less
    "avanti",     # = forward
    "centro",     # = center
    "giro",       # = lap
    "tempo",      # = time
    "turno",      # = turn
}

# Motorsport loanwords acceptable in Italian
MOTORSPORT_TERMS = {
    "pit", "pit stop", "pitstop", "pit lane", "pit wall",
    "box",
    "safety car",
    "pace car",  # acceptable motorsport term
    "undercut", "overcut",
    "stint",
    "setup", "set-up",
    "delta",
    "deploy", "harvest",
    "drs", "ers", "kers",
    "virtual",
    "ok",
    "sprint",
    "pole", "pole position",
    "rally",
    "slick", "slicks",
    "full wet",
    "inter", "inters",
    "spotter",
    "team",
    "team radio",
    "drive-through", "drive through",
    "stop-and-go", "stop-go", "stop and go",
    "warm up", "warm-up",
    "cool down", "cool-down",
    "push",
    "flat", "flat spot",
    "lock", "lock-up",
    "graining", "blistering",
    "aero",
    "performance",
    "attack mode",
    "mode",
    "map",
    "software", "hardware",
    "update", "upgrade",
    "check",
    "personal best",
    "gt", "gt3", "gt4", "gte", "lmp", "lmp2",
    "dtm",
    "endurance",
    "class",
    "hypercar",
    "prototype",
    "formula",
    "grip",
    "draft", "drafting",
    "tow",
    "replay",
    "record",
    "leader", # used in Italian racing too
    "gap", # used in Italian racing too
    "top", # "top speed" used in Italian
    "sector", # settore is used but "sector" also common
    "chicane",
    "bus stop",  # famous corner name at Spa
    "hook",      # corner name component
}

# Track/corner proper names - these should not be flagged
# We'll detect these by checking if a phrase is entirely English AND seems like a proper noun


def is_corner_or_track_name(text):
    """Detect if the entire subtitle is a track/corner name (proper nouns, typically Title Case)."""
    text = text.strip()
    # If most words start with uppercase, it's likely a proper name
    words = text.split()
    if not words:
        return False
    # Common corner name patterns
    if any(w.lower() in ("hairpin", "corner", "bend", "straight", "kink", "chicane",
                          "turn", "curve", "loop", "hook", "hill", "dip", "crest",
                          "bridge", "esses", "complex") for w in words):
        # If it contains a corner descriptor, likely a corner name
        caps = sum(1 for w in words if w[0].isupper() or w.lower() in ("the", "of", "in", "before", "after", "at"))
        if caps >= len(words) * 0.5:
            return True
    # If it's all Title Case words, might be a name
    if all(w[0].isupper() or w.lower() in ("the", "of", "in", "di", "del", "della", "delle", "dei") for w in words if len(w) > 1):
        if len(words) >= 1 and len(words) <= 6:
            return True
    return False


def detect_english_issues(text):
    """
    Detect genuinely problematic English in Italian text.
    Returns list of (issue_description, suggestion) tuples.
    """
    if not text or not text.strip():
        return []

    text_stripped = text.strip()
    text_lower = text_stripped.lower()
    issues = []

    # Skip if it's a corner/track name
    if is_corner_or_track_name(text_stripped):
        return []

    # Tokenize
    words = re.findall(r"[a-zA-Z']+", text_lower)

    # ===== PATTERN 1: Clearly English standalone words in otherwise Italian text =====
    # These are words that have NO Italian meaning and should have been translated

    clearly_english = {
        "job": "lavoro",
        "well done": "ben fatto/bravo",
        "good job": "ottimo lavoro",
        "nice one": "bella/ben fatto",
        "great": "ottimo/grande (agg.)",
        "awesome": "fantastico",
        "amazing": "incredibile",
        "brilliant": "brillante",
        "buddy": "amico",
        "mate": "amico/compagno",
        "guy": "ragazzo/tipo",
        "guys": "ragazzi",
        "sorry": "scusa",
        "please": "per favore",
        "thank": "grazie",
        "thanks": "grazie",
        "careful": "attento",
        "watch out": "attento/stai attento",
        "look out": "attento",
        "keep": "mantieni",
        "keeping": "mantenendo",
        "slow down": "rallenta",
        "speed up": "accelera",
        "don't worry": "non preoccuparti",
        "looking good": "va bene/stai andando bene",
        "behind you": "dietro di te",
        "overall": "complessivo/in totale",
        "currently": "attualmente",
        "actually": "in realta'",
        "basically": "fondamentalmente",
        "probably": "probabilmente",
        "maybe": "forse",
        "perhaps": "forse",
        "definitely": "sicuramente",
        "remember": "ricorda",
        "listen": "ascolta",
        "alright": "va bene",
        "enough": "abbastanza",
        "almost": "quasi",
        "never": "mai",
        "always": "sempre",
        "because": "perche'",
        "yellow": "giallo/gialla",
        "green": "verde",
        "blue": "blu",
        "white": "bianco/bianca",
        "black": "nero/nera",
        "damage": "danno/danni",
        "fuel": "carburante",
        "tire": "gomma",
        "tyre": "gomma",
        "tires": "gomme",
        "tyres": "gomme",
        "brake": "freno/frena",
        "brakes": "freni",
        "braking": "frenata",
        "throttle": "acceleratore",
        "engine": "motore",
        "battery": "batteria",
        "gearbox": "cambio",
        "suspension": "sospensione/sospensioni",
        "wing": "ala/alettone",
        "bodywork": "carrozzeria",
        "cooling": "raffreddamento",
        "oil": "olio",
        "water": "acqua",
        "weather": "meteo",
        "rain": "pioggia",
        "dry": "asciutto",
        "wet": "bagnato",
        "pressure": "pressione",
        "wear": "usura/consumo",
        "degradation": "degrado",
        "strategy": "strategia",
        "window": "finestra",
        "target": "obiettivo",
        "penalty": "penalita'",
        "warning": "avvertimento/avviso",
        "caution": "prudenza/attenzione",
        "qualifying": "qualifiche",
        "practice": "prove libere",
        "session": "sessione",
        "championship": "campionato",
        "points": "punti",
        "podium": "podio",
        "information": "informazione",
        "driver": "pilota",
        "teammate": "compagno di squadra",
        "circuit": "circuito",
        "track": "pista",
        "race": "gara",
        "faster": "piu' veloce",
        "slower": "piu' lento",
        "quicker": "piu' rapido",
        "closing": "avvicinandosi",
        "catching": "raggiungendo",
        "pulling": "allontanandosi",
        "losing": "perdendo",
        "gaining": "guadagnando",
        "fighting": "combattendo/lottando",
        "attacking": "attaccando",
        "defending": "difendendo",
        "leading": "in testa",
        "following": "seguendo",
        "spinning": "testacoda/in rotazione",
        "crashing": "incidente",
        "crash": "incidente",
        "accident": "incidente",
        "contact": "contatto",
        "wrong": "sbagliato",
        "perfect": "perfetto",
        "excellent": "eccellente",
        "terrible": "terribile",
        "horrible": "orribile",
        "good": "buono/bene",
        "nice": "bello/ben",
        "bad": "male/cattivo",
        "new": "nuovo",
        "old": "vecchio",
        "big": "grande",
        "small": "piccolo",
        "long": "lungo",
        "short": "corto",
        "high": "alto",
        "low": "basso",
        "fast": "veloce",
        "slow": "lento",
        "better": "migliore/meglio",
        "worse": "peggiore/peggio",
        "best": "migliore",
        "worst": "peggiore",
        "right": "destra/giusto",
        "left": "sinistra",
        "inside": "interno",
        "outside": "esterno",
        "ahead": "davanti",
        "behind": "dietro",
        "straight": "rettilineo/dritto",
        "corner": "curva",
        "corners": "curve",
        "lap": "giro",
        "laps": "giri",
        "position": "posizione",
        "speed": "velocita'",
        "time": "tempo",
        "times": "tempi",
        "minute": "minuto",
        "minutes": "minuti",
        "hour": "ora",
        "hours": "ore",
        "start": "partenza/inizio",
        "finish": "traguardo/fine",
        "flag": "bandiera",
        "grid": "griglia",
        "formation": "formazione",
        "restart": "ripartenza",
        "compound": "mescola",
        "intermediate": "intermedia",
        "balance": "bilanciamento",
        "downforce": "carico",
        "drag": "resistenza",
        "floor": "fondo",
        "retire": "ritirarsi",
        "win": "vittoria/vincere",
        "lose": "perdere",
        "apex": "apice/corda",
        "curb": "cordolo",
        "kerb": "cordolo",
        "hairpin": "tornante",
        "hundred": "cento",
        "thousand": "mille",
    }

    # Check multi-word phrases first
    multi_word_english = {
        "well done": "ben fatto/bravo",
        "good job": "ottimo lavoro",
        "nice one": "bella/ben fatto",
        "good work": "buon lavoro",
        "keep it up": "continua cosi'",
        "watch out": "attento/stai attento",
        "look out": "attento",
        "slow down": "rallenta",
        "speed up": "accelera",
        "hold on": "tieni duro",
        "let's go": "andiamo/forza",
        "right now": "adesso/subito",
        "don't worry": "non preoccuparti",
        "looking good": "va bene",
        "behind you": "dietro di te",
        "in front": "davanti",
        "a win": "una vittoria",
    }

    found_words = set()

    for phrase, suggestion in multi_word_english.items():
        if phrase in text_lower:
            # Verify it's not part of a motorsport term
            if not any(mt in text_lower for mt in MOTORSPORT_TERMS if phrase in mt):
                issues.append((phrase, suggestion, "frase inglese"))
                for w in phrase.split():
                    found_words.add(w)

    # Check individual words
    for word in words:
        word_clean = word.strip("'").lower()

        if len(word_clean) <= 2:
            continue
        if word_clean in found_words:
            continue
        if word_clean in ITALIAN_WORDS_LIKE_ENGLISH:
            continue
        if word_clean in MOTORSPORT_TERMS:
            continue

        # Check if word is part of a motorsport multi-word term
        is_motorsport = False
        for term in MOTORSPORT_TERMS:
            if ' ' in term or '-' in term:
                term_words = re.findall(r"[a-z]+", term)
                if word_clean in term_words and term.replace('-', ' ') in text_lower.replace('-', ' '):
                    is_motorsport = True
                    break
        if is_motorsport:
            continue

        if word_clean in clearly_english:
            issues.append((word_clean, clearly_english[word_clean], "parola inglese"))
            found_words.add(word_clean)

    # ===== PATTERN 2: Detect number words in English =====
    number_words = {
        "one": "uno", "two": "due", "three": "tre", "four": "quattro",
        "five": "cinque", "six": "sei", "seven": "sette", "eight": "otto",
        "nine": "nove", "ten": "dieci", "twenty": "venti", "thirty": "trenta",
        "forty": "quaranta", "fifty": "cinquanta", "sixty": "sessanta",
        "seventy": "settanta", "eighty": "ottanta", "ninety": "novanta",
        "hundred": "cento", "thousand": "mille",
    }
    for word in words:
        wc = word.strip("'").lower()
        if wc in found_words:
            continue
        if wc in number_words:
            issues.append((wc, number_words[wc], "numero in inglese"))
            found_words.add(wc)

    # ===== PATTERN 3: Detect English pronouns/articles in otherwise Italian text =====
    # Only flag these if the surrounding text is Italian
    english_function_words = {
        "your": "tuo/il tuo",
        "you": "tu",
        "we're": "siamo/stiamo",
        "you're": "sei/stai",
        "i'm": "sono/sto",
        "they're": "sono/stanno",
        "it's": "e'",
        "that's": "e'/quello e'",
        "there's": "c'e'",
        "he's": "lui e'",
        "she's": "lei e'",
        "don't": "non",
        "doesn't": "non",
        "can't": "non puoi",
        "won't": "non + futuro",
        "isn't": "non e'",
        "aren't": "non sono",
        "wasn't": "non era",
        "weren't": "non erano",
        "haven't": "non ho/hai",
        "hasn't": "non ha",
        "didn't": "non + passato",
        "couldn't": "non poteva",
        "shouldn't": "non dovrebbe",
        "wouldn't": "non vorrebbe",
    }

    for word in words:
        wc = word.strip("'").lower()
        if wc in found_words:
            continue
        if wc in english_function_words:
            # Check if there are Italian words in the same sentence
            italian_indicators = ["il ", "la ", "lo ", "le ", "gli ", "un ", "una ",
                                  " di ", " del ", " dei ", " che ", " non ", " sono ",
                                  " sta ", " hai ", " hai", " sei ", " e' ", " piu ",
                                  " con ", " per ", " nella ", " nel ", " sul ",
                                  " alla ", " giro", " giri", " curva", " pista"]
            has_italian = any(ind in text_lower for ind in italian_indicators)
            if has_italian:
                issues.append((wc, english_function_words[wc], "parola funzionale inglese in frase italiana"))
                found_words.add(wc)

    # ===== PATTERN 4: Detect entirely English phrases (not corner names) =====
    # If most words in the text are English, the whole thing might be untranslated
    # But skip short texts and corner names
    if len(words) >= 3 and not is_corner_or_track_name(text_stripped):
        eng_count = 0
        ita_count = 0
        for w in words:
            wc = w.strip("'").lower()
            if len(wc) <= 2:
                continue
            if wc in ITALIAN_WORDS_LIKE_ENGLISH:
                ita_count += 1
            elif wc in clearly_english or wc in number_words or wc in english_function_words:
                eng_count += 1
            # Words not in either dict are ambiguous - count as Italian
            # (better to have false negatives than false positives)

    return issues


def process_csv(filepath):
    """Process a CSV file and return findings."""
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)

            for line_num, row in enumerate(reader, start=2):
                if len(row) < 3:
                    continue

                audio_path = row[0] if len(row) > 0 else ""
                audio_filename = row[1] if len(row) > 1 else ""
                subtitle = row[2] if len(row) > 2 else ""
                text_for_tts = row[3] if len(row) > 3 else ""
                original_english = row[4] if len(row) > 4 else ""

                all_findings = {}

                sub_issues = detect_english_issues(subtitle)
                if sub_issues:
                    all_findings["subtitle"] = (subtitle, sub_issues)

                tts_issues = detect_english_issues(text_for_tts)
                if tts_issues:
                    all_findings["text_for_tts"] = (text_for_tts, tts_issues)

                if all_findings:
                    results.append({
                        "file": filepath,
                        "line": line_num,
                        "audio_path": audio_path,
                        "audio_filename": audio_filename,
                        "subtitle": subtitle,
                        "text_for_tts": text_for_tts,
                        "original_english": original_english,
                        "findings": all_findings,
                    })
    except FileNotFoundError:
        print(f"[ATTENZIONE] File non trovato: {filepath}")
    except Exception as e:
        print(f"[ERRORE] Elaborazione {filepath}: {e}")

    return results


def print_results(all_results):
    """Print all findings in a readable format."""
    total_phrases = 0
    total_english_words = 0
    files_summary = defaultdict(int)
    word_frequency = defaultdict(int)

    print("=" * 100)
    print("AUDIT TRADUZIONI VOICE PACK ITALIANO - PAROLE INGLESI NON TRADOTTE (v2)")
    print("=" * 100)

    # Group by category
    categories = defaultdict(list)
    for result in all_results:
        # Extract category from audio path
        path_parts = result["audio_path"].replace("\\", "/").strip("/").split("/")
        if len(path_parts) >= 2:
            cat = "/".join(path_parts[:3]) if len(path_parts) >= 3 else "/".join(path_parts)
        else:
            cat = result["audio_path"]
        categories[cat].append(result)

    for cat in sorted(categories.keys()):
        results_in_cat = categories[cat]
        print("")
        print(f"### CATEGORIA: {cat} ({len(results_in_cat)} frasi) ###")

        for result in results_in_cat:
            total_phrases += 1
            filepath_short = result["file"].split("/")[-1]
            files_summary[filepath_short] += 1

            print("")
            print("-" * 90)
            print(f"  File:     {filepath_short} (riga {result['line']})")
            print(f"  Path:     {result['audio_path']}")
            print(f"  Filename: {result['audio_filename']}")
            if result['original_english']:
                print(f"  English:  {result['original_english']}")

            for col_name, (text, findings) in result["findings"].items():
                print(f"  [{col_name}]: \"{text}\"")
                for eng_word, ita_suggestion, issue_type in findings:
                    total_english_words += 1
                    word_frequency[eng_word] += 1
                    print(f"    >>> [{issue_type}] \"{eng_word}\"  -->  \"{ita_suggestion}\"")

    print("")
    print("=" * 100)
    print("RIEPILOGO GENERALE")
    print("=" * 100)
    print(f"  Frasi problematiche trovate: {total_phrases}")
    print(f"  Parole/frasi inglesi totali: {total_english_words}")
    print("")
    print("  Per file:")
    for fname, count in sorted(files_summary.items()):
        print(f"    {fname}: {count} frasi problematiche")
    print("")
    print("  Parole inglesi piu' frequenti:")
    for word, count in sorted(word_frequency.items(), key=lambda x: -x[1])[:30]:
        print(f"    \"{word}\": {count} occorrenze")
    print("")
    print("=" * 100)


def main():
    files = [
        "C:/Users/utente/Documents/-crewchief-ita-voicepack/lexicon/phrase_inventory_ita.csv",
        "C:/Users/utente/Documents/-crewchief-ita-voicepack/lexicon/lmu_specific_phrases.csv",
        "C:/Users/utente/Documents/-crewchief-ita-voicepack/lexicon/custom_phrases.csv",
        "C:/Users/utente/Documents/-crewchief-ita-voicepack/lexicon/swear_phrases.csv",
        "C:/Users/utente/Documents/-crewchief-ita-voicepack/lexicon/phrase_inventory_missing.csv",
    ]

    all_results = []

    for f in files:
        print(f"Analisi di: {f.split('/')[-1]}")
        results = process_csv(f)
        all_results.extend(results)
        print(f"  -> {len(results)} frasi con problemi trovate")

    print("")
    print_results(all_results)


if __name__ == "__main__":
    main()
