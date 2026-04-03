#!/usr/bin/env python3
"""Fix remaining mixed Italian/English phrases in phrase_inventory_ita.csv.

Fixes:
1. Mixed ITA/ENG phrases (~1084 entries with English grammar + Italian words)
2. Missing articles/prepositions for natural Italian
3. Numbers: "mille and" -> "mille e"

Does NOT touch already-correct translations.
"""

import csv
import re
import sys
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "lexicon" / "phrase_inventory_ita.csv"
BACKUP_PATH = CSV_PATH.with_suffix(".csv.bak_v2")

# ============================================================================
# EXACT REPLACEMENTS: subtitle AND text_for_tts columns
# Key = (audio_path_contains, old_text) -> new_text
# These fix specific phrases identified as mixed ITA/ENG
# ============================================================================

# We fix by matching subtitle+text_for_tts content exactly
EXACT_FIXES: dict[str, str] = {
    # === MANDATORY PIT STOPS ===
    # confirm_alternate_tyres
    "copy that, alternate gomme": "ricevuto, gomme alternate",
    "understood, siamo putting alternate gomme on": "capito, montiamo gomme alternate",
    "ok, alternate gomme": "ok, gomme alternate",
    "acknowledged, alternate gomme this time": "ricevuto, gomme alternate questa volta",
    "ok, siamo putting alternate gomme on": "ok, montiamo gomme alternate",
    # confirm_change_all_tyres
    "copy that, we'll change all 4 gomme": "ricevuto, cambiamo tutte e 4 le gomme",
    "understood, siamo changing all 4 gomme": "capito, cambiamo tutte e 4 le gomme",
    "acknowledged, we'll change all 4 gomme": "ricevuto, cambiamo tutte e 4 le gomme",
    "understood, we'll change all your gomme": "capito, cambiamo tutte le gomme",
    "copy that, we'll change all your gomme": "ricevuto, cambiamo tutte le gomme",
    # confirm_change_front_tyres
    "understood, siamo changing front gomme only this time": "capito, cambiamo solo le gomme anteriori questa volta",
    "copy that, front gomme only": "ricevuto, solo le anteriori",
    "acknowledged, we'll change front gomme this time": "ricevuto, cambiamo le anteriori questa volta",
    "acknowledged, siamo changing front gomme only this time": "ricevuto, cambiamo solo le anteriori questa volta",
    "understood, change front gomme only": "capito, solo le gomme anteriori",
    "acknowledged, siamo changing your front gomme only": "ricevuto, cambiamo solo le tue anteriori",
    # confirm_change_left_side_tyres
    "acknowledged, we'll change left side gomme only": "ricevuto, cambiamo solo le gomme del lato sinistro",
    # confirm_change_no_tyres
    "copy that, no gomme at the next stop": "ricevuto, niente gomme alla prossima sosta",
    "acknowledged, no gomme at the next pit stop": "ricevuto, niente gomme al prossimo pit stop",
    "copy that, no gomma change at the next stop": "ricevuto, niente cambio gomme alla prossima sosta",
    "understood, no gomme for the next pit stop": "capito, niente gomme al prossimo pit stop",
    # confirm_change_rear_tyres
    "copy that, we'll change rear gomme only": "ricevuto, cambiamo solo le posteriori",
    "understood, siamo changing your rear gomme only": "capito, cambiamo solo le tue posteriori",
    "ok, we'll change your rear gomme only": "ok, cambiamo solo le tue posteriori",
    "acknowledged, we'll change the rear gomme only": "ricevuto, cambiamo solo le posteriori",
    "copy that, siamo changing rear gomme only": "ricevuto, cambiamo solo le posteriori",
    "understood, rear gomme only": "capito, solo le posteriori",
    # confirm_change_right_side_tyres
    "acknowledged, we'll change right side gomme only": "ricevuto, cambiamo solo le gomme del lato destro",
    # confirm_change_tyres
    "acknowledged, we'll change gomme": "ricevuto, cambiamo le gomme",
    # confirm_dry_tyres
    "acknowledged, asciutto gomme": "ricevuto, gomme da asciutto",
    # confirm_fit_tyre_set_intro
    "acknowledged, we'll fit gomma set": "ricevuto, montiamo il set di gomme",
    # confirm_dont_fix_aero
    "copy that, no aerodinamica fixes this time": "ricevuto, niente riparazioni aerodinamiche questa volta",
    "acknowledged, no aerodinamica fix at the next pit stop": "ricevuto, niente riparazioni aerodinamiche al prossimo pit",
    "copy that, no aerodinamica fixes": "ricevuto, niente riparazioni aerodinamiche",
    # confirm_fix_all_aero
    "understood, we'll fix front and rear aerodinamica": "capito, ripariamo l'aerodinamica anteriore e posteriore",
    "copy that, we'll fix your front and your rear aerodinamica": "ricevuto, ripariamo la tua aerodinamica anteriore e posteriore",
    "acknowledged, we'll fix front and rear aerodinamica": "ricevuto, ripariamo l'aerodinamica anteriore e posteriore",
    "ok, we'll fix your front and your rear aerodinamica": "ok, ripariamo la tua aerodinamica anteriore e posteriore",
    "understood, we'll fix the front and rear aerodinamica": "capito, ripariamo l'aerodinamica anteriore e posteriore",
    # confirm_fix_body
    "acknowledged, we'll fix the carrozzeria": "ricevuto, ripariamo la carrozzeria",
    # confirm_fix_front_aero
    "acknowledged, we'll fix the front aerodinamica": "ricevuto, ripariamo l'aerodinamica anteriore",
    "copy that, we'll fix your front aerodinamica": "ricevuto, ripariamo la tua aerodinamica anteriore",
    "understood, we'll fix the front aerodinamica": "capito, ripariamo l'aerodinamica anteriore",
    # confirm_fix_rear_aero
    "acknowledged, we'll fix the rear aerodinamica": "ricevuto, ripariamo l'aerodinamica posteriore",
    "copy that, we'll fix your rear aerodinamica": "ricevuto, ripariamo la tua aerodinamica posteriore",
    "understood, we'll fix the rear aerodinamica": "capito, ripariamo l'aerodinamica posteriore",
    # confirm_fix_suspension
    "acknowledged, we'll fix the sospensione": "ricevuto, ripariamo le sospensioni",
    "copy that, we'll fix your sospensione": "ricevuto, ripariamo le tue sospensioni",
    "understood, we'll fix the sospensione": "capito, ripariamo le sospensioni",
    # confirm_hard_tyres
    "acknowledged, hard gomme": "ricevuto, gomme dure",
    "siamo going for hard gomme": "montiamo gomme dure",
    "ok, we'll put hard gomme on": "ok, montiamo le gomme dure",
    "ok we'll put hard gomme on": "ok montiamo le gomme dure",
    "understood, hard gomme": "capito, gomme dure",
    "hard gomme": "gomme dure",
    "copy that, hard gomme": "ricevuto, gomme dure",
    # confirm_hyper_soft_tyres
    "acknowledged, hyper-soft gomme": "ricevuto, gomme hyper-soft",
    "hyper-soft gomme": "gomme hyper-soft",
    "copy that, hyper-soft gomme": "ricevuto, gomme hyper-soft",
    "understood, hyper-soft gomme": "capito, gomme hyper-soft",
    # confirm_intermediate_tyres
    "acknowledged, intermediate gomme": "ricevuto, gomme intermedie",
    "intermediate gomme": "gomme intermedie",
    "siamo going for intermediate gomme": "montiamo gomme intermedie",
    "ok, we'll put intermediate gomme on": "ok, montiamo le intermedie",
    "understood, intermediate gomme": "capito, gomme intermedie",
    "copy that, intermediate gomme": "ricevuto, gomme intermedie",
    # confirm_medium_tyres
    "acknowledged, medium gomme": "ricevuto, gomme medie",
    "medium gomme": "gomme medie",
    "siamo going for medium gomme": "montiamo gomme medie",
    "ok we'll put medium gomme on": "ok montiamo le gomme medie",
    "ok, we'll put medium gomme on": "ok, montiamo le gomme medie",
    "understood, medium gomme": "capito, gomme medie",
    "copy that, medium gomme": "ricevuto, gomme medie",
    # confirm_monsoon_tyres
    "acknowledged, monsoon gomme": "ricevuto, gomme da monsone",
    "monsoon gomme": "gomme da monsone",
    "copy that, monsoon gomme": "ricevuto, gomme da monsone",
    "understood, monsoon gomme": "capito, gomme da monsone",
    # confirm_next_compound
    "next gomma compound": "prossima mescola",
    "copy that, next gomma compound": "ricevuto, prossima mescola",
    "acknowledged, next gomma compound": "ricevuto, prossima mescola",
    # confirm_no_refueling
    "no carburante this time": "niente carburante questa volta",
    "we won't add carburante": "non aggiungiamo carburante",
    "no refueling this time": "niente rifornimento questa volta",
    "acknowledged, no carburante": "ricevuto, niente carburante",
    "copy that, no carburante this time": "ricevuto, niente carburante questa volta",
    "understood, no carburante": "capito, niente carburante",
    "understood, no refueling this time": "capito, niente rifornimento questa volta",
    # confirm_option_tyres
    "we'll go for option gomme": "montiamo gomme option",
    "that's option gomme": "gomme option",
    "siamo going for option gomme": "montiamo gomme option",
    "acknowledged, option gomme": "ricevuto, gomme option",
    "copy that, option gomme": "ricevuto, gomme option",
    # confirm_prime_tyres
    "siamo going for prime gomme": "montiamo gomme prime",
    "we'll put prime gomme on": "montiamo le gomme prime",
    "acknowledged, prime gomme": "ricevuto, gomme prime",
    "copy that, prime gomme": "ricevuto, gomme prime",
    "understood, prime gomme": "capito, gomme prime",
    # confirm_refueling
    "we'll add carburante": "aggiungiamo carburante",
    "siamo gonna add carburante": "aggiungiamo carburante",
    "acknowledged, we'll add carburante": "ricevuto, aggiungiamo carburante",
    "understood, siamo adding carburante": "capito, aggiungiamo carburante",
    "copy that, we'll add carburante": "ricevuto, aggiungiamo carburante",
    # confirm_those_arent_available
    "those gomme aren't available": "quelle gomme non sono disponibili",
    "sorry, those gomme aren't available": "mi dispiace, quelle gomme non sono disponibili",
    # confirm_soft_tyres
    "acknowledged, soft gomme": "ricevuto, gomme morbide",
    "siamo going for soft gomme": "montiamo gomme morbide",
    "we'll put soft gomme on": "montiamo le gomme morbide",
    "soft gomme this time": "gomme morbide questa volta",
    "soft gomme": "gomme morbide",
    "copy that, soft gomme": "ricevuto, gomme morbide",
    "understood, soft gomme": "capito, gomme morbide",
    # confirm_super_soft_tyres
    "acknowledged, super-soft gomme": "ricevuto, gomme super-soft",
    "super-soft gomme": "gomme super-soft",
    "copy that, super-soft gomme": "ricevuto, gomme super-soft",
    # confirm_ultra_soft_tyres
    "acknowledged, ultra-soft gomme": "ricevuto, gomme ultra-soft",
    "ultra-soft gomme": "gomme ultra-soft",
    "copy that, ultra-soft gomme": "ricevuto, gomme ultra-soft",
    # confirm_wet_tyres
    "acknowledged, bagnato gomme": "ricevuto, gomme da bagnato",
    "bagnato gomme": "gomme da bagnato",
    "copy that, bagnato gomme": "ricevuto, gomme da bagnato",
    "understood, bagnato gomme": "capito, gomme da bagnato",
    # no_refueling_no_tyres
    "no refueling and no gomme": "niente rifornimento e niente gomme",
    "siamo not changing gomme": "non cambiamo le gomme",
    "no gomme this time": "niente gomme questa volta",
    "no gomme and no carburante": "niente gomme e niente carburante",
    "acknowledged, no gomme and no carburante": "ricevuto, niente gomme e niente carburante",
    # combined pit stops
    "siamo gonna change all 4 gomme and siamo gonna refuel you": "cambiamo tutte e 4 le gomme e facciamo rifornimento",
    "siamo adding carburante and siamo gonna change all 4 gomme": "aggiungiamo carburante e cambiamo tutte e 4 le gomme",
    "siamo changing all 4 gomme, no carburante this time": "cambiamo tutte e 4 le gomme, niente carburante questa volta",
    "siamo changing all 4 gomme, no refueling": "cambiamo tutte e 4 le gomme, niente rifornimento",
    "siamo changing front gomme only": "cambiamo solo le gomme anteriori",
    "siamo changing rear gomme only": "cambiamo solo le gomme posteriori",
    "siamo changing front gomme only, and siamo refueling": "cambiamo solo le anteriori e facciamo rifornimento",
    "siamo changing rear gomme only, and siamo refueling": "cambiamo solo le posteriori e facciamo rifornimento",
    "siamo changing front gomme only, no carburante": "cambiamo solo le anteriori, niente carburante",
    "siamo changing rear gomme only, no carburante": "cambiamo solo le posteriori, niente carburante",
    "we'll need to pit for carburante": "dovremo fermarci per il carburante",
    "we'll need to pit for carburante by giro": "dovremo fermarci per il carburante entro il giro",
    "we'll need to pit to refuel by giro": "dovremo fermarci per rifornimento entro il giro",
    "we'll need to refuel by giro": "dovremo rifornire entro il giro",
    "siamo refueling only, no gomme": "solo rifornimento, niente gomme",
    "siamo refueling only, no gomma change": "solo rifornimento, niente cambio gomme",

    # === FLAGS ===
    "siamo running dietro the safety macchina": "siamo dietro la safety car",
    "safety macchina phase": "fase safety car",
    "the safety macchina's out, yellow flag": "la safety car e' in pista, bandiera gialla",
    "yellow flag, safety macchina phase": "bandiera gialla, fase safety car",
    "full course yellow, siamo under caution": "gialla totale, siamo in regime di cautela",
    "siamo under caution, full course yellow": "siamo in regime di cautela, gialla totale",
    "siamo under caution": "siamo in regime di cautela",
    "siamo going green next time by": "si riparte al prossimo passaggio",
    "siamo going green": "si riparte",
    "safety macchina out": "safety car in pista",
    "safety macchina's coming out": "esce la safety car",
    "pace macchina's out": "la pace car e' in pista",
    "abbiamo a full course yellow": "abbiamo una gialla totale",
    "abbiamo a full course caution": "abbiamo una cautela totale",
    "abbiamo double yellows, double yellows": "doppie gialle, doppie gialle",
    "green flag, siamo racing": "bandiera verde, si corre",
    "pits are closed": "i box sono chiusi",
    "box ora aperti": "i box ora sono aperti",
    "lead giro vehicles can now pit": "i veicoli del giro di testa possono rientrare ai box",
    "lead giro cars can pit": "le macchine del giro di testa possono rientrare",
    "ok, you're clear to pass": "ok, puoi sorpassare",
    "ok, puoi overtake": "ok, puoi sorpassare",
    "settore 1 is clear": "il settore 1 e' libero",
    "settore 2 is clear": "il settore 2 e' libero",
    "settore 3 is clear": "il settore 3 e' libero",
    "green flag settore 1": "bandiera verde settore 1",
    "green flag settore 2": "bandiera verde settore 2",
    "green flag settore 3": "bandiera verde settore 3",
    "settore 1 is yellow": "il settore 1 e' giallo",
    "settore 2 is yellow": "il settore 2 e' giallo",
    "settore 3 is yellow": "il settore 3 e' giallo",
    "yellow flag davanti": "bandiera gialla davanti",
    "incident up davanti": "incidente davanti",
    "yellow flag in settore 1": "bandiera gialla nel settore 1",
    "yellow flag in settore 2": "bandiera gialla nel settore 2",
    "yellow flag in settore 3": "bandiera gialla nel settore 3",
    "stay alta": "resta in alto",
    "stay dietro": "resta dietro",
    "rimani dietro la pace car": "resta dietro la pace car",
    "hold posizione dietro": "mantieni la posizione dietro",
    "you've passed under yellow": "hai sorpassato in regime di gialla",
    "siamo shown the black flag": "ci hanno mostrato la bandiera nera",
    "black flag, siamo being shown the black flag": "bandiera nera, ci stanno mostrando la bandiera nera",
    "pensiamo p5's gone off": "pensiamo che la P5 sia uscita",

    # slow car / stopped car in turns
    "slow macchina in turn 1": "macchina lenta in curva 1",
    "slow macchina in turn 2": "macchina lenta in curva 2",
    "slow macchina in turn 3": "macchina lenta in curva 3",
    "slow macchina in turn 4": "macchina lenta in curva 4",
    "slow macchina in turn 5": "macchina lenta in curva 5",
    "slow macchina in turn 6": "macchina lenta in curva 6",
    "slow macchina in turn 7": "macchina lenta in curva 7",
    "slow macchina in turn 8": "macchina lenta in curva 8",
    "slow macchina in turn 9": "macchina lenta in curva 9",
    "slow macchina in turn 10": "macchina lenta in curva 10",
    "slow macchina ahead": "macchina lenta davanti",
    "macchina stopped in turn 1": "macchina ferma in curva 1",
    "macchina stopped in turn 2": "macchina ferma in curva 2",
    "macchina stopped in turn 3": "macchina ferma in curva 3",
    "macchina stopped in turn 4": "macchina ferma in curva 4",
    "macchina stopped in turn 5": "macchina ferma in curva 5",
    "macchina stopped in turn 6": "macchina ferma in curva 6",
    "macchina stopped in turn 7": "macchina ferma in curva 7",
    "macchina stopped in turn 8": "macchina ferma in curva 8",
    "macchina stopped in turn 9": "macchina ferma in curva 9",
    "macchina stopped in turn 10": "macchina ferma in curva 10",
    "macchina stopped ahead": "macchina ferma davanti",

    # === DAMAGE REPORTING ===
    "that's buono to know, thanks,": "bene a sapersi, grazie",
    "that's buono to know": "bene a sapersi",
    "ok, , thanks for the update": "ok, grazie per l'aggiornamento",
    "ok, i can't hear you, maybe the radio's gone": "ok, non ti sento, forse la radio e' andata",
    "can't hear anything, , think you've knackered the radio": "non sento niente, penso che la radio sia andata",
    "ok, sounds like you're all right": "ok, sembra che tu stia bene",
    "sounds like you're ok, thanks,": "sembra che tu stia bene, grazie",
    "buono to hear you're ok": "bene sentirti stare bene",
    "i assume that means you're ok, thanks,": "presumo che significhi che stai bene, grazie",
    "answer me if puoi?": "rispondimi se puoi",
    "come on, siamo all shitting ourselves here, tell us you're ok": "dai, siamo tutti in ansia qui, dicci che stai bene",
    "if puoi hear me, help's coming": "se mi senti, i soccorsi stanno arrivando",
    "hai us all really worried here, man": "ci hai fatto preoccupare tutti qui",
    "fucking hell, man, i hope you're ok": "cazzo, spero che tu stia bene",
    "we've lost the motore, it's over": "abbiamo perso il motore, e' finita",
    "the motore's fucked, nicely done,": "il motore e' fottuto, bel lavoro",
    "the sospensione's boogered": "le sospensioni sono distrutte",
    "trasmissione's completely screwed, that's our gara done": "la trasmissione e' completamente andata, la nostra gara e' finita",
    "looks like hai some minor carrozzeria danno": "sembra che tu abbia qualche danno minore alla carrozzeria",
    "siamo seeing some minor brake danno": "vediamo qualche danno minore ai freni",
    "your carrozzeria looks buono": "la carrozzeria sembra a posto",
    "your carrozzeria's fine": "la carrozzeria e' a posto",
    "your carrozzeria's ok": "la carrozzeria va bene",
    "motore looks fine": "il motore sembra a posto",
    "your sospensione's fine": "le sospensioni sono a posto",
    "the trasmissione looks fine": "la trasmissione sembra a posto",
    "the trasmissione's ok": "la trasmissione va bene",
    "hai a right rear puncture": "hai una foratura posteriore destra",

    # === ENGINE MONITOR ===
    "your water temperatura looks quite alta": "la temperatura dell'acqua sembra piuttosto alta",
    "ok, , your carburante pressione's dropping": "ok, la pressione del carburante sta scendendo",
    "you have bassa carburante pressione": "hai la pressione del carburante bassa",
    "abbiamo a carburante pressione attenzione here": "abbiamo un avviso di pressione carburante",
    "your carburante pressione's dropping": "la pressione del carburante sta scendendo",
    "bassa carburante pressione": "pressione carburante bassa",
    "looks like abbiamo oil pressione issues": "sembra che abbiamo problemi di pressione dell'olio",
    "siamo seeing a bassa oil pressione attenzione here": "vediamo un avviso di bassa pressione dell'olio",
    "siamo seeing a bassa oil pressione attenzione": "vediamo un avviso di bassa pressione dell'olio",
    "looks like hai oil pressione issues here": "sembra che tu abbia problemi di pressione dell'olio",

    # === FUEL ===
    "very little carburante left": "pochissimo carburante rimasto",
    "it'll close on giro": "si chiudera' al giro",
    "and it'll close on giro": "e si chiudera' al giro",
    "5 minutes of carburante remaining": "5 minuti di carburante rimasti",
    "that's 5 minutes of carburante left": "sono 5 minuti di carburante rimasti",
    "hai about 4 giri of carburante left": "hai circa 4 giri di carburante rimasti",
    "we estimate 4 giri carburante remaining": "stimiamo 4 giri di carburante rimasti",
    "hai about 3 giri of carburante left": "hai circa 3 giri di carburante rimasti",
    "3 giri of carburante remaining": "3 giri di carburante rimasti",
    "only 2 giri of carburante left": "solo 2 giri di carburante rimasti",
    "2 minutes of carburante remaining": "2 minuti di carburante rimasti",
    "gallons per giro": "galloni per giro",
    "hai half a gallon left": "hai mezzo gallone rimasto",
    "siamo ok on carburante": "siamo a posto col carburante",
    "the carburante's ok": "il carburante va bene",
    "carburante looks buono": "il carburante sembra a posto",
    "you're looking buono for carburante": "sei messo bene col carburante",
    "abbiamo plenty of carburante": "abbiamo carburante in abbondanza",
    "carburante levels are fine": "i livelli di carburante sono ok",
    "looks like you're gonna need to save some carburante": "sembra che dovrai risparmiare un po' di carburante",
    "dovrai to save some carburante": "dovrai risparmiare un po' di carburante",
    "you've used half your carburante": "hai usato meta' del carburante",
    "hai half your carburante left": "ti rimane meta' del carburante",
    "into the gara": "nella gara",
    "giri of carburante remaining": "giri di carburante rimasti",
    "giri of carburante left": "giri di carburante rimasti",
    "liters per giro": "litri per giro",
    "minutes of carburante remaining": "minuti di carburante rimasti",
    "minutes of carburante left": "minuti di carburante rimasti",
    "hai 1 gallon left": "hai un gallone rimasto",
    "we'll need to pit for carburante by giro": "dovremo fermarci per il carburante entro il giro",
    "we'll need to pit to refuel by giro": "dovremo fermarci per rifornimento entro il giro",
    "we'll need to refuel by giro": "dovremo rifornire entro il giro",
    "pensiamo our refueling window will open after": "pensiamo che la finestra di rifornimento si apra dopo",
    "our carburante window will open after": "la nostra finestra carburante si apre dopo",
    "our carburante window opens on giro": "la nostra finestra carburante si apre al giro",
    "our refueling window opens on giro": "la finestra di rifornimento si apre al giro",
    "hai loads of carburante": "hai un sacco di carburante",
    "10 minutes of carburante remaining": "10 minuti di carburante rimasti",
    "hai 10 minutes of carburante remaining": "hai 10 minuti di carburante rimasti",
    "pensiamo we'll need": "pensiamo che dovremo",
    "pensiamo we'll need to add": "pensiamo che dovremo aggiungere",
    "pensiamo we'll need to stop again": "pensiamo che dovremo fermarci di nuovo",

    # === TYRE MONITOR ===
    "hai cold freni all around, be careful": "hai i freni freddi su tutte le ruote, fai attenzione",
    "gomma temps are buono": "le temperature delle gomme sono buone",
    "gomma temperature are buono": "le temperature delle gomme sono buone",
    "option": "opzione",

    # === CONDITIONS ===
    "air and track temperature are increasing": "le temperature dell'aria e della pista stanno aumentando",
    "air and track temperature are rising": "le temperature dell'aria e della pista stanno salendo",
    "air temperatura is now": "la temperatura dell'aria e' ora",
    "abbiamo drizzle now and it's drying out": "abbiamo pioggerella e si sta asciugando",
    "no more pioggia": "non piove piu'",
    "the track temperatura's now": "la temperatura della pista e' ora",

    # === FROZEN ORDER / POSITION ===
    "pass the pace macchina": "sorpassa la pace car",
    "pass the safety macchina": "sorpassa la safety car",
    "the pace macchina": "la pace car",
    "the safety macchina": "la safety car",
    "rolling start": "partenza lanciata",
    "standing start": "partenza da fermo",

    # === DRIVER SWAPS ===
    "siamo pitting now for a pilota change": "rientriamo ai box per il cambio pilota",

    # === OPPONENTS / WATCHED ===
    "your rivale's pitting from posizione": "il tuo rivale sta rientrando ai box dalla posizione",
    "your compagno di squadra's pitting from posizione": "il tuo compagno di squadra sta rientrando dalla posizione",
    "your rivale": "il tuo rivale",
    "your compagno di squadra": "il tuo compagno di squadra",

    # === CODRIVER (pace notes) ===
    "open tornante sinistra": "tornante sinistra largo",
    "open tornante destra": "tornante destra largo",
    "si chiude bad": "si chiude male",
    "full taglia": "taglia completa",
    "half lunga": "mezza lunga",
    "keep sinistra": "tieni sinistra",
    "keep destra": "tieni destra",

    # === NUMBERS ===
    "mille and": "mille e",

    # === MISC PATTERNS ===
    "alternate": "alternata",

    # === CODRIVER ===
    "don't taglia anticipata": "non tagliare anticipata",
    "don't taglia ritardata": "non tagliare ritardata",
    "very lunga": "molto lunga",

    # === CONDITIONS ===
    "this pioggia's really heavy now, and getting harder, take care": "la pioggia e' molto forte e sta peggiorando, fai attenzione",
    "e' properly pissing it down qui": "sta diluviando qui",
    "siamo starting to see some pioggia": "iniziamo a vedere un po' di pioggia",

    # === DAMAGE REPORTING (residui) ===
    "there's some minor sospensione danno": "c'e' qualche danno minore alle sospensioni",
    "there's no significant danno": "non ci sono danni significativi",
    "macchina's looking buono, no danno": "la macchina sembra a posto, nessun danno",
    "non stiamo seeing any sospensione danno": "non vediamo danni alle sospensioni",
    "la tua sospensione's looking pretty brutto": "le tue sospensioni sembrano messe piuttosto male",
    "it'll polish out, , forget about it": "si sistema da solo, non preoccuparti",

    # === FLAGS (residui) ===
    "safety macchina's out, pits are closed": "la safety car e' in pista, i box sono chiusi",
    "siamo under caution, pits are closed": "siamo in regime di cautela, i box sono chiusi",
    "full course yellow, lead giro vehicles can now pit": "gialla totale, i veicoli del giro di testa possono rientrare ai box",
    "pace macchina still out, lead giro cars can pit": "la pace car e' ancora in pista, le macchine del giro di testa possono rientrare",
    "pace macchina's coming in, be ready": "la pace car sta rientrando, preparati",
    "pace macchina's coming in, get ready": "la pace car sta rientrando, tieniti pronto",
    "full course yellow, safety macchina's coming out": "gialla totale, esce la safety car",
    "safety macchina's coming out, full course yellow": "esce la safety car, gialla totale",
    "safety macchina's coming out, yellow flag": "esce la safety car, bandiera gialla",
    "pace macchina is out, siamo under caution": "la pace car e' in pista, siamo in regime di cautela",
    "ok, you've passed under yellow, devi to give back": "ok, hai sorpassato in regime di gialla, devi restituire la posizione",
    "you've passed under yellow, devi to give back": "hai sorpassato in regime di gialla, devi restituire la posizione",
    "you've passed under yellow flag, devi to give back": "hai sorpassato in regime di bandiera gialla, devi restituire la posizione",
    "pensiamo it might be": "pensiamo che potrebbe essere",
    "there's a slow macchina davanti": "c'e' una macchina lenta davanti",
    "there's a macchina stopped davanti": "c'e' una macchina ferma davanti",
    "abbiamo un stopped macchina davanti": "c'e' una macchina ferma davanti",
    "there's a stopped macchina davanti": "c'e' una macchina ferma davanti",
    "macchina stopped turn 4, stay alta": "macchina ferma in curva 4, resta in alto",

    # === FROZEN ORDER ===
    "line up single-file dietro": "mettiti in fila indiana dietro",
    "line up single-file dietro macchina number": "mettiti in fila indiana dietro la macchina numero",
    "line up single-file dietro macchina": "mettiti in fila indiana dietro la macchina",
    "siamo starting from pole": "partiamo dalla pole",
    "siamo starting from posizione": "partiamo dalla posizione",

    # === FUEL (residui) ===
    "siamo running on fumes": "stiamo andando a vapori",

    # === MANDATORY PIT STOPS (residui) ===
    # confirm_fix patterns con "we'll fix"
    "we'll fix the front aerodinamica": "ripariamo l'aerodinamica anteriore",
    "we'll fix your front aerodinamica": "ripariamo la tua aerodinamica anteriore",
    "we'll fix the rear aerodinamica": "ripariamo l'aerodinamica posteriore",
    "we'll fix your rear aerodinamica": "ripariamo la tua aerodinamica posteriore",
    "we'll fix the sospensione": "ripariamo le sospensioni",
    "we'll fix your sospensione": "ripariamo le tue sospensioni",
    "we'll fix the carrozzeria": "ripariamo la carrozzeria",
    "we'll fix your carrozzeria": "ripariamo la tua carrozzeria",
    "we'll fix everything we can": "ripariamo tutto il possibile",
    "acknowledged, we'll fix everything": "ricevuto, ripariamo tutto",

    # === CONDITIONS (residui v2) ===
    "the pioggia's absolutely terrible qui, be careful": "la pioggia e' terribile qui, fai attenzione",
    "e' properly pissing it down qui": "sta diluviando qui",
    "the track temperatura's decreasing, e' now": "la temperatura della pista sta scendendo, e' ora",
    "the track temperatura's falling, e' now": "la temperatura della pista sta calando, e' ora",
    "the track temperatura's increasing, e' now": "la temperatura della pista sta salendo, e' ora",
    "the track temperatura's rising, e' now": "la temperatura della pista sta aumentando, e' ora",
    "abbiamo light pioggia qui, getting harder": "abbiamo pioggia leggera qui, sta peggiorando",
    "siamo getting proper pioggia now, sembra che e' getting harder": "sta piovendo forte adesso, sembra che stia peggiorando",
    "stiamo vedendo some pioggia": "stiamo vedendo un po' di pioggia",

    # === DAMAGE (residui v2) ===
    "the macchina's looking buono, no danno": "la macchina sembra a posto, nessun danno",
    "your sospensione looks fine": "le sospensioni sembrano a posto",
    "non stiamo seeing any danno alle sospensioni": "non vediamo danni alle sospensioni",
    "the trasmissione looks fine": "la trasmissione sembra a posto",
    "your sospensione's looking piuttosto brutto": "le sospensioni sembrano messe piuttosto male",

    # === FUEL (residui v2) ===
    "it'll end on giro": "finira' al giro",
    "siamo half-way home, siamo ok on carburante": "siamo a meta' gara, col carburante siamo a posto",
    "half-distance, the carburante's ok": "meta' distanza, il carburante va bene",
    "half-distance, looking buono for carburante": "meta' distanza, il carburante sembra a posto",
    "half-distance, carburante levels are fine": "meta' distanza, i livelli di carburante sono ok",
    "half-distance, sembra che gonna need to save some carburante": "meta' distanza, sembra che dovrai risparmiare carburante",
    "half-carburante, hai used half your carburante": "meta' carburante, hai usato meta' del carburante",
    "only 2 more giri of carburante": "solo 2 giri di carburante rimasti",

    # === LAP COUNTER ===
    "ok, the finish, well done": "ok, il traguardo, ben fatto",
    "c'e' the finish, buono drive": "ecco il traguardo, bella guida",
    "and c'e' the finish, buono result, , well done": "ed ecco il traguardo, buon risultato, ben fatto",
    "ok the end, buono finish, , well done": "ok la fine, buon piazzamento, ben fatto",
    "form up dietro": "mettiti in fila dietro",
    "line up dietro": "mettiti in fila dietro",
    "ok, get ready": "ok, preparati",
    "get ready, , e' hammer time": "preparati, e' ora di spingere",
    "ok, , get ready": "ok, preparati",
    "get ready": "preparati",
    "ok, , get ready, relax": "ok, preparati, rilassati",
    "one more giro, p1": "ancora un giro, primo",
    "last giro, looking buono for a podium": "ultimo giro, sembra buono per un podio",
    "the gara leader's crossed the line": "il leader della gara ha tagliato il traguardo",
    "white flag, one more giro": "bandiera bianca, ancora un giro",

    # === LAP TIMES ===
    "the fastest giro": "il giro piu' veloce",
    "buono consistency, keep 'em coming": "buona costanza, continua cosi'",
    "decent giro, but puoi go quicker": "buon giro, ma puoi andare piu' veloce",
    "pace is davvero buono": "il ritmo e' davvero buono",
    "pace is ottimo": "il ritmo e' ottimo",
    "pace is ok": "il ritmo va bene",
    "your fastest giro today": "il tuo giro piu' veloce oggi",
    "buono giro, your quickest so far": "buon giro, il piu' veloce finora",
    "buono giro, your quickest today": "buon giro, il piu' veloce di oggi",
    "your fastest giro": "il tuo giro piu' veloce",
    "your quickest giro": "il tuo giro piu' veloce",
    "losing 2 decimi in sectors 1 and 2": "perdi 2 decimi nei settori 1 e 2",
    "sectors 1 and 3 sono buone": "i settori 1 e 3 sono buoni",
    "2 decimi down in sectors 1 and 3": "2 decimi in meno nei settori 1 e 3",
    "settore 1 time is quick": "il tempo nel settore 1 e' veloce",
    "settore 2 and 3 are piuttosto buono": "i settori 2 e 3 sono piuttosto buoni",
    "settore 2 and 3 are fast": "i settori 2 e 3 sono veloci",
    "quickest in settore 2 and 3": "il piu' veloce nei settori 2 e 3",
    "losing 2 decimi in sectors 2 and 3": "perdi 2 decimi nei settori 2 e 3",
    "sectors 2 and 3 are 2 decimi down": "i settori 2 e 3 sono 2 decimi in meno",
    "settore 2 time is ok": "il tempo nel settore 2 va bene",
    "settore 2 is fastest": "il settore 2 e' il piu' veloce",
    "settore 3 time is quick": "il tempo nel settore 3 e' veloce",
    "settore 3 time is fast": "il tempo nel settore 3 e' veloce",
    "2 decimi down in all 3 sectors": "2 decimi in meno in tutti e 3 i settori",
    "siamo quickest at the moment": "siamo i piu' veloci al momento",
    "siamo current setting the pace": "al momento stiamo dettando il ritmo",
    "siamo setting the pace": "stiamo dettando il ritmo",
    "your giro time was": "il tuo tempo sul giro era",

    # === MANDATORY PIT STOPS (v2) ===
    "box this giro for options": "ai box questo giro per le option",
    "pit this giro for options": "ai box questo giro per le option",
    "box this giro for prime gomme": "ai box questo giro per le gomme prime",
    "box this giro for primes": "ai box questo giro per le prime",
    "pit this giro for prime gomme": "ai box questo giro per le gomme prime",
    "puoi now fit option gomme": "ora puoi montare le gomme option",
    "puoi put options on": "puoi montare le option",
    "puoi now put primes on": "ora puoi montare le prime",
    "puoi now fit prime gomme": "ora puoi montare le gomme prime",
    "ricevuto, fix the front aerodinamica": "ricevuto, ripariamo l'aerodinamica anteriore",
    "capito, siamo fixing the front aerodinamica": "capito, ripariamo l'aerodinamica anteriore",
    "ok, siamo gonna fix the front aerodinamica": "ok, ripariamo l'aerodinamica anteriore",
    "ricevuto, fix the front aerodinamica only": "ricevuto, ripariamo solo l'aerodinamica anteriore",
    "capito, siamo fixing rear aerodinamica only": "capito, ripariamo solo l'aerodinamica posteriore",
    "ricevuto, rear aerodinamica only": "ricevuto, solo l'aerodinamica posteriore",
    "ricevuto, fix the rear aerodinamica only": "ricevuto, ripariamo solo l'aerodinamica posteriore",
    "ok, fix rear aerodinamica only at the next stop": "ok, ripariamo solo l'aerodinamica posteriore alla prossima sosta",
    "capito, siamo fixing the rear aerodinamica only": "capito, ripariamo solo l'aerodinamica posteriore",
    "capito, fix the sospensione at the next stop": "capito, ripariamo le sospensioni alla prossima sosta",
    "ricevuto, fix the sospensione": "ricevuto, ripariamo le sospensioni",
    "ok, siamo gonna fix the sospensione at the next stop": "ok, ripariamo le sospensioni alla prossima sosta",
    "ok, siamo gonna fix the sospensione": "ok, ripariamo le sospensioni",
    "ricevuto, siamo gonna fix the sospensione at the next stop": "ricevuto, ripariamo le sospensioni alla prossima sosta",
    "ok, no refueling this time": "ok, niente rifornimento questa volta",
    "capito, go for option gomme": "capito, montiamo le option",
    "capito, siamo gonna add carburante": "capito, aggiungiamo carburante",
    "ok, add the carburante": "ok, aggiungiamo il carburante",
    "ricevuto, siamo gonna refuel you": "ricevuto, facciamo rifornimento",
    "capito, soft gomme this time": "capito, gomme morbide questa volta",
    "non stiamo refueling": "non facciamo rifornimento",
    "non stiamo gonna refuel": "non facciamo rifornimento",
    "non stiamo refueling and non stiamo changing gomme": "non facciamo rifornimento e non cambiamo le gomme",
    "non stiamo changing any gomme": "non cambiamo le gomme",
    "non stiamo changing our gomme": "non cambiamo le gomme",
    "the pit window opens next giro": "la finestra pit si apre il prossimo giro",
    "siamo serving the penalita'": "stiamo scontando la penalita'",
    "be serving the penalita'": "scontiamo la penalita'",
    "siamo gonna change all 4 gomme and refuel": "cambiamo tutte e 4 le gomme e facciamo rifornimento",
    "stiamo cambiando all 4 gomme and siamo gonna add carburante": "cambiamo tutte e 4 le gomme e aggiungiamo carburante",
    "stiamo cambiando all 4 gomme and stiamo aggiungendo carburante": "cambiamo tutte e 4 le gomme e aggiungiamo carburante",
    "add carburante and change all 4 gomme": "aggiungiamo carburante e cambiamo tutte e 4 le gomme",
    "siamo gonna change all 4 gomme": "cambiamo tutte e 4 le gomme",
    "stiamo cambiando your front gomme only": "cambiamo solo le tue anteriori",
    "stiamo cambiando front gomme only this time": "cambiamo solo le anteriori questa volta",
    "change the front gomme only": "cambiamo solo le anteriori",
    "change your rear gomme only": "cambiamo solo le tue posteriori",
    "stiamo cambiando the rear gomme only": "cambiamo solo le posteriori",
    "stiamo cambiando rear gomme only this time": "cambiamo solo le posteriori questa volta",
    "siamo gonna fix the front aerodinamica": "ripariamo l'aerodinamica anteriore",
    "fix the front and leave the rear aerodinamica": "ripariamo l'anteriore e lasciamo l'aerodinamica posteriore",
    "siamo gonna fix the front aerodinamica and leave the rear": "ripariamo l'aerodinamica anteriore e lasciamo la posteriore",
    "siamo gonna fix the front aerodinamica only": "ripariamo solo l'aerodinamica anteriore",
    "siamo fixing front aerodinamica only": "ripariamo solo l'aerodinamica anteriore",
    "fix the front aerodinamica and leave the rear": "ripariamo l'anteriore e lasciamo la posteriore",
    "siamo gonna fix your front and rear aerodinamica": "ripariamo la tua aerodinamica anteriore e posteriore",
    "fix the front and rear aerodinamica": "ripariamo l'aerodinamica anteriore e posteriore",
    "fix the front and the rear aerodinamica": "ripariamo l'aerodinamica anteriore e posteriore",
    "siamo fixing front and rear aerodinamica": "ripariamo l'aerodinamica anteriore e posteriore",
    "siamo gonna fix the rear aerodinamica": "ripariamo l'aerodinamica posteriore",

    # === TIMINGS ===
    "davanti is now": "il distacco davanti e' ora",
    "dietro is increasing, e' now": "il distacco dietro sta crescendo, e' ora",
    "dietro is now": "il distacco dietro e' ora",
    "non wait too long, find that distacco": "non aspettare troppo, trova il distacco",
    "non be distracted, defend your posizione": "non distrarti, difendi la tua posizione",
    "let's see how wide puoi make this thing": "vediamo quanto riesci ad allargare il distacco",
    "pulling away, il distacco dietro is now": "ti stai staccando, il distacco dietro e' ora",
    "pulling away from the guy dietro, il distacco's now": "ti stai staccando da quello dietro, il distacco e' ora",
    "il distacco dietro is now": "il distacco dietro e' ora",
    "il distacco davanti is increasing, il distacco is now": "il distacco davanti sta crescendo, il distacco e' ora",
    "il distacco davanti has increased, e' now about": "il distacco davanti e' aumentato, e' ora circa",
    "il distacco davanti is now": "il distacco davanti e' ora",
    "in, il distacco is now": "si avvicina, il distacco e' ora",
    "is closing in, il distacco is now": "si sta avvicinando, il distacco e' ora",
    "is getting closer, il distacco is now": "si sta avvicinando, il distacco e' ora",
    "the pilota davanti's reputation isn't ottimo": "il pilota davanti non ha una gran reputazione",
    "the guy dietro's davvero accident-prone, be careful qui": "quello dietro e' davvero incline agli incidenti, fai attenzione",
    "the guy dietro's davvero accident-prone, be careful": "quello dietro e' davvero incline agli incidenti, fai attenzione",
    "the guy dietro's reputation isn't ottimo": "quello dietro non ha una gran reputazione",
    "the guy dietro doesn't gara molto clean": "quello dietro non corre molto pulito",

    # === TYRE MONITOR ===
    "let's get some heat into these freni": "scaldiamo un po' questi freni",
    "hai cold front gomme": "hai le gomme anteriori fredde",
    "left side gomme are cold": "le gomme del lato sinistro sono fredde",
    "cooking your front gomme": "stai cuocendo le gomme anteriori",
    "cooking your left front gomma": "stai cuocendo l'anteriore sinistra",
    "cooking your left rear gomma": "stai cuocendo la posteriore sinistra",
    "your left rear's cooking": "la tua posteriore sinistra si sta cuocendo",
    "cooking your left side gomme": "stai cuocendo le gomme del lato sinistro",
    "your rear freni have overheated, they're davvero hot": "i freni posteriori si sono surriscaldati, sono davvero caldi",
    "cooking your rear gomme": "stai cuocendo le gomme posteriori",
    "cooking your right front gomma": "stai cuocendo l'anteriore destra",
    "cooking your right rear gomma": "stai cuocendo la posteriore destra",
    "cooking your right side gomme": "stai cuocendo le gomme del lato destro",
    "hai damaged both front gomme": "hai danneggiato entrambe le gomme anteriori",
    "hai damaged your left front gomma": "hai danneggiato l'anteriore sinistra",
    "hai damaged your left rear gomma": "hai danneggiato la posteriore sinistra",
    "hai damaged both rear gomme": "hai danneggiato entrambe le gomme posteriori",
    "hai damaged your right front gomma": "hai danneggiato l'anteriore destra",
    "hai damaged your right rear gomma": "hai danneggiato la posteriore destra",
    "your gomma usura looks fine": "l'usura delle gomme sembra a posto",
    "non stiamo seeing any significant gomma usura": "non vediamo usura significativa sulle gomme",
    "front gomme are hot, fronts are hot": "le gomme anteriori sono calde",
    "left rear gomma looks a little hot": "la posteriore sinistra sembra un po' calda",
    "your left side gomme hot": "le gomme del lato sinistro sono calde",
    "your right front gomma's getting hot": "l'anteriore destra si sta scaldando",
    "right side gomme are hot": "le gomme del lato destro sono calde",
    "gonna need new gomme all around": "serviranno gomme nuove su tutte le ruote",
    "your front gomme have gone": "le tue gomme anteriori sono finite",
    "your left front gomma looks knackered": "l'anteriore sinistra sembra distrutta",
    "that left rear gomma's shot": "la posteriore sinistra e' andata",
    "that right front gomma looks knackered": "l'anteriore destra sembra distrutta",
    "your right rear's completely worn out": "la tua posteriore destra e' completamente consumata",
    "pensiamo you'll get about": "pensiamo che otterrai circa",
    "pensiamo dovresti get about": "pensiamo che dovresti ottenere circa",
    "your left front pressione looks quite alta": "la pressione dell'anteriore sinistra sembra piuttosto alta",
    "your left front pressione looks quite bassa": "la pressione dell'anteriore sinistra sembra piuttosto bassa",
    "your left front pressione looks ok": "la pressione dell'anteriore sinistra va bene",
    "your left front pressione looks molto alta": "la pressione dell'anteriore sinistra sembra molto alta",
    "your left front pressione looks molto bassa": "la pressione dell'anteriore sinistra sembra molto bassa",
    "your left rear pressione looks ok": "la pressione della posteriore sinistra va bene",
    "your right front pressione looks ok": "la pressione dell'anteriore destra va bene",
    "your right rear pressione looks ok": "la pressione della posteriore destra va bene",
    "stiamo vedendo front locking going into": "vediamo bloccaggio delle anteriori in ingresso alla",
    "stiamo vedendo lots of front locking": "vediamo molto bloccaggio delle anteriori",
    "locking your front freni": "stai bloccando i freni anteriori",
    "stiamo vedendo lots of left rear locking": "vediamo molto bloccaggio della posteriore sinistra",
    "stiamo vedendo rear locking into": "vediamo bloccaggio delle posteriori in",
    "stiamo vedendo lots of rear brake locking": "vediamo molto bloccaggio dei freni posteriori",
    "stiamo vedendo lots of rear locking": "vediamo molto bloccaggio delle posteriori",
    "stiamo vedendo right front locking into": "vediamo bloccaggio dell'anteriore destra in",
    "stiamo vedendo lots of front right locking": "vediamo molto bloccaggio dell'anteriore destra",
    "stiamo vedendo lots of right rear locking": "vediamo molto bloccaggio della posteriore destra",
    "more minutes on these gomme": "piu' minuti con queste gomme",
    "stiamo vedendo left rear wheel spin in": "vediamo pattinamento della posteriore sinistra in",
    "stiamo vedendo lots of rear left wheel spin": "vediamo molto pattinamento della posteriore sinistra",
    "stiamo vedendo loads of rear left wheel spin": "vediamo tantissimo pattinamento della posteriore sinistra",
    "stiamo vedendo lots of rear wheel spin": "vediamo molto pattinamento delle posteriori",
    "spinning your rear right gomma": "stai facendo pattinare la posteriore destra",
    "stiamo vedendo lots of rear right wheel spin": "vediamo molto pattinamento della posteriore destra",
    "c'e' some usura on those front gomme": "c'e' un po' di usura sulle gomme anteriori",
    "your left rear's showing some significant usura": "la posteriore sinistra mostra un'usura significativa",
    "stiamo vedendo significant usura on both left side gomme": "vediamo un'usura significativa su entrambe le gomme del lato sinistro",
    "siamo looking at significant usura on those rear gomme": "vediamo un'usura significativa sulle gomme posteriori",
    "your right front's carrying some usura now": "l'anteriore destra ha un po' di usura adesso",
    "lookout for your right rear gomma, , e' looking piuttosto worn": "attenzione alla tua posteriore destra, sembra piuttosto consumata",

    # === WATCHED OPPONENTS ===
    "capito, no more monitoring of macchina number": "capito, non monitoriamo piu' la macchina numero",
    "ok, no more monitoring of our rivale": "ok, non monitoriamo piu' il nostro rivale",
    "ricevuto, no more monitoring of our compagno di squadra": "ricevuto, non monitoriamo piu' il nostro compagno di squadra",
    "ok, no more monitoring of our compagno di squadra": "ok, non monitoriamo piu' il nostro compagno di squadra",

    # === PENALTIES ===
    "give back": "restituisci",

    # === MULTICLASS ===
    "faster class macchina": "macchina di classe piu' veloce",
    "slower class macchina": "macchina di classe piu' lenta",
    "faster class macchina behind": "macchina di classe piu' veloce dietro",
    "slower class macchina ahead": "macchina di classe piu' lenta davanti",

    # === STRATEGY ===
    "siamo on the wrong gomme": "siamo sulle gomme sbagliate",
    "siamo on the wrong gomme for these conditions": "siamo sulle gomme sbagliate per queste condizioni",
    "dovresti be coming out into clear air": "dovresti uscire in aria pulita",
    "pensiamo you'll be exiting the pits into clear air": "pensiamo che uscirai dai box in aria pulita",
    "is pitting from posizione": "sta rientrando ai box dalla posizione",

    # === MULTICLASS ===
    "there's a faster macchina approaching": "c'e' una macchina piu' veloce in arrivo",
    "there's a faster class macchina approaching": "c'e' una macchina di classe superiore in arrivo",
    "there's a faster class macchina dietro": "c'e' una macchina di classe superiore dietro",
    "there's a faster macchina dietro, he's class leader": "c'e' una macchina piu' veloce dietro, e' il leader di classe",
    "faster macchina dietro, they're racing us for posizione, there'll be no blue flag": "macchina piu' veloce dietro, sta lottando con noi per la posizione, niente bandiera blu",
    "c'e' a faster macchina approaching, lui e' racing us for posizione, non expect a blue flag": "c'e' una macchina piu' veloce in arrivo, sta lottando con noi per la posizione, non aspettarti la bandiera blu",
    "faster macchina approaching, they're racing us for posizione - non expect and blue flag": "macchina piu' veloce in arrivo, sta lottando con noi per la posizione, niente bandiera blu",
    "faster macchina approaching, lui e' racing us for posizione, non expect a blue flag": "macchina piu' veloce in arrivo, sta lottando per la posizione, non aspettarti la bandiera blu",
    "faster macchina dietro, lui e' racing us for posizione, non expect a blue flag": "macchina piu' veloce dietro, sta lottando per la posizione, non aspettarti la bandiera blu",
    "there's some faster cars approaching, their fighting for posizione": "ci sono macchine piu' veloci in arrivo, stanno lottando per la posizione",
    "faster cars approaching, they're battling for posizione, the group includes the class leader": "macchine piu' veloci in arrivo, stanno lottando per la posizione, nel gruppo c'e' il leader di classe",
    "c'e' some faster cars approaching, they're fighting for posizione, the group includes the class lead": "ci sono macchine piu' veloci in arrivo, stanno lottando per la posizione, nel gruppo c'e' il leader di classe",
    "slower class macchina davanti, he's their class leader": "macchina di classe inferiore davanti, e' il loro leader di classe",
    "slower macchina davanti, lui e' the class leader for these guys": "macchina piu' lenta davanti, e' il leader di classe per loro",
    "approaching some slower cars, these guys are fighting for posizione": "ci avviciniamo a macchine piu' lente, stanno lottando per la posizione",
    "slow cars davanti, including the class leader": "macchine lente davanti, incluso il leader di classe",

    # === OPPONENTS ===
    "davanti is pitting": "quello davanti sta rientrando ai box",
    "dietro is pitting": "quello dietro sta rientrando ai box",
    "dietro is pitting no": "quello dietro sta rientrando ai box",
    "i non posso pronounce the name": "non riesco a pronunciare il nome",
    "the macchina davanti's pitting": "la macchina davanti sta rientrando ai box",
    "the macchina davanti's pitting now": "la macchina davanti sta rientrando ai box adesso",
    "the macchina dietro's pitting now": "la macchina dietro sta rientrando ai box adesso",
    "the macchina dietro's pitting": "la macchina dietro sta rientrando ai box",

    # === OVERTAKING AIDS ===
    "hai no more push-to-pass": "non hai piu' push-to-pass",
    "hai one more push-to-pass": "hai ancora un push-to-pass",
    "ok, push-to-pass is now available": "ok, il push-to-pass e' ora disponibile",

    # === PEARLS OF WISDOM ===
    "we need quali-pace every giro now, , there might ancora be chances qui": "servono tempi da qualifica ogni giro adesso, potrebbero ancora esserci possibilita'",
    "nice and smooth, non overdrive the macchina": "fluido e preciso, non forzare la macchina",

    # === PENALTIES ===
    "track limits, the giro non count": "limiti di pista, il giro non conta",
    "hai cut the track, they're gonna delete the giro and they'll delete the next one, too": "hai tagliato la pista, cancelleranno il giro e anche il prossimo",
    "we've had another attenzione about track limits": "abbiamo avuto un altro avviso sui limiti di pista",
    "we've done more giri than siamo allowed qui, we've been disqualified": "abbiamo fatto piu' giri di quelli consentiti, siamo stati squalificati",
    "abbiamo a drive-through for a false start": "abbiamo un drive-through per partenza anticipata",
    "drive-through penalita' for a false-start": "penalita' drive-through per partenza anticipata",
    "hai cut the track, they'll delete the giro": "hai tagliato la pista, cancelleranno il giro",
    "your penalita''s completed": "la tua penalita' e' completata",
    "hai served your penalita'": "hai scontato la tua penalita'",
    "pit now for your drive-through penalita'": "ai box adesso per la tua penalita' drive-through",
    "pit for your stop-go penalita' now, box, box, box": "ai box per la tua penalita' stop-go adesso, box box box",
    "box, box, box for this stop-go penalita'": "box box box per questa penalita' stop-go",
    "box, box, box, pit now for your penalita'": "box box box, ai box adesso per la tua penalita'",
    "stiamo andando too slowly, speed up": "stiamo andando troppo piano, accelera",
    "stiamo andando the wrong way": "stiamo andando nella direzione sbagliata",

    # === POSITION ===
    "our pace should be ok, siamo aiming for around p": "il nostro ritmo dovrebbe essere ok, puntiamo alla posizione",
    "dovresti win this, the clear favourite": "dovresti vincere, sei il chiaro favorito",
    "awful start, , but non give up": "partenza terribile, ma non mollare",
    "terrible start, , but the rest isn't over, yet": "partenza terribile, ma la gara non e' finita",
    "fucking hell, nightmare start , danno limitation from qui": "cazzo, partenza da incubo, limitiamo i danni da qui",
    "fucking bollocks start, , e' danno limitation from qui": "cazzo di partenza, limitiamo i danni da qui",

    # === PUSH NOW ===
    "heads up, there's a macchina rejoining": "attenzione, c'e' una macchina che rientra in pista",
    "there's a macchina rejoining": "c'e' una macchina che rientra in pista",
    "there's a macchina rejoining davanti": "c'e' una macchina che rientra davanti",
    "the uscita box looks clear": "l'uscita box sembra libera",
    "uscita box is clear": "l'uscita box e' libera",
    "uscita box's clear, non cross the white line": "l'uscita box e' libera, non attraversare la linea bianca",
    "the uscita box's clear": "l'uscita box e' libera",
    "the uscita box looks clear": "l'uscita box sembra libera",
    "there's traffic dietro": "c'e' traffico dietro",
    "take care, there's a macchina approaching": "attenzione, c'e' una macchina in arrivo",
    "there's traffic dietro, take care": "c'e' traffico dietro, fai attenzione",

    # === RACE TIME ===
    "siamo at the half-way point": "siamo a meta' gara",
    "1 more giro, p1": "ancora un giro, primo",
    "1 more giro after this one": "ancora un giro dopo questo",

    # === SPOTTER ===
    "macchina down bassa": "macchina in basso",
    "siamo 3 wide, down bassa": "siamo 3 in fila, in basso",
    "3 wide, down bassa": "3 in fila, in basso",
    "down bassa, 3 wide": "in basso, 3 in fila",
    "siamo up alta, 3 wide": "siamo in alto, 3 in fila",
    "3 wide, up alta": "3 in fila, in alto",
    "up alta, 3 wide": "in alto, 3 in fila",
}

# ============================================================================
# REGEX-BASED FIXES for patterns that appear with variations
# ============================================================================

REGEX_FIXES: list[tuple[str, str]] = [
    # "siamo going for X gomme" -> "montiamo le gomme X"
    (r"siamo going for (\w+) gomme", r"montiamo gomme \1"),
    # "we'll put X gomme on" -> "montiamo le gomme X"
    (r"we'll put (\w+) gomme on", r"montiamo le gomme \1"),
    # General: "siamo" used as "we're" in English sentences
    (r"\bsiamo going\b", "stiamo andando"),
    (r"\bsiamo adding\b", "stiamo aggiungendo"),
    (r"\bsiamo changing\b", "stiamo cambiando"),
    (r"\bsiamo putting\b", "stiamo mettendo"),
    (r"\bsiamo seeing\b", "stiamo vedendo"),
    (r"\bsiamo not\b", "non stiamo"),
    (r"\bsiamo running\b", "stiamo correndo"),
    (r"\bsiamo starting\b", "stiamo partendo"),
    (r"\bsiamo under\b", "siamo in regime di"),
    # "abbiamo a" -> "abbiamo un/una"
    (r"\babbiamo a (\w+)", r"abbiamo un \1"),
    # "hai" used with English constructs
    (r"\bhai some\b", "hai qualche"),
    (r"\bhai about\b", "hai circa"),
    # "looks like" patterns
    (r"\blooks like\b", "sembra che"),
    # "pensiamo" + English
    (r"\bpensiamo that\b", "pensiamo che"),
    (r"\bpensiamo it\b", "pensiamo che"),
    (r"\bpensiamo we\b", "pensiamo che"),
    # "devi to" -> "devi"
    (r"\bdevi to\b", "devi"),
    # "dovrai to" -> "dovrai"
    (r"\bdovrai to\b", "dovrai"),
    # Common English in Italian context
    (r"\bcopy that\b", "ricevuto"),
    (r"\backnowledged\b", "ricevuto"),
    (r"\bunderstood\b", "capito"),
    (r"\bdon't\b", "non"),
    (r"\bwon't\b", "non"),
    (r"\bcan't\b", "non posso"),
    # "safety macchina" -> "safety car"
    (r"\bsafety macchina\b", "safety car"),
    (r"\bpace macchina\b", "pace car"),
    # "stopped macchina" -> "macchina ferma"
    (r"\bstopped macchina\b", "macchina ferma"),
    # "slow macchina" -> "macchina lenta"
    (r"\bslow macchina\b", "macchina lenta"),
    # "X danno" -> "danno X" (wrong word order)
    (r"\bsospensione danno\b", "danno alle sospensioni"),
    (r"\bcarrozzeria danno\b", "danno alla carrozzeria"),
    (r"\bbrake danno\b", "danno ai freni"),
    (r"\baero danno\b", "danno aerodinamico"),
    (r"\bminor danno\b", "danno minore"),
    # "buono" in English context
    (r"\blooks buono\b", "sembra a posto"),
    (r"\blooked buono\b", "sembrava a posto"),
    (r"\bare buono\b", "sono buone"),
    (r"\bis buono\b", "e' buono"),
    # Remaining English words
    (r"\bwe'll\b", ""),
    (r"\bwe're\b", ""),
    (r"\byou're\b", ""),
    (r"\byou've\b", "hai"),
    (r"\bi'm\b", "sono"),
    (r"\bthat's\b", ""),
    (r"\bit's\b", "e'"),
    (r"\bthere's\b", "c'e'"),
    (r"\bhe's\b", "lui e'"),
    (r"\bmate\b", ""),
    (r"\bthanks\b", "grazie"),
    (r"\bplease\b", "per favore"),
    (r"\bstill \b", "ancora "),
    (r"\bhere\b", "qui"),
    (r"\bvery \b", "molto "),
    (r"\breally \b", "davvero "),
    (r"\bpretty \b", "piuttosto "),
    (r"\bjust \b", ""),
    # "lead giro" -> "giro di testa"
    (r"\blead giro\b", "giro di testa"),
    # "full course yellow" -> "gialla totale"
    (r"\bfull course yellow\b", "gialla totale"),
    # "single-file" -> "fila indiana"
    (r"\bsingle-file\b", "in fila indiana"),
    # "line up" -> "mettiti in fila"
    (r"\bline up\b", "mettiti in fila"),
    # "pits are closed" -> "i box sono chiusi"
    (r"\bpits are closed\b", "i box sono chiusi"),
    # "on fumes" -> "a vapori"
    (r"\bon fumes\b", "a vapori"),
    # "cooking your X gomma/gomme" patterns
    (r"\bcooking your\b", "stai cuocendo le tue"),
    (r"\bcooking\b", "stai surriscaldando"),
    # "X's cooking" -> "si sta surriscaldando"
    (r"'s cooking\b", " si sta surriscaldando"),
    # "hai damaged" -> "hai danneggiato"
    (r"\bhai damaged\b", "hai danneggiato"),
    # "X looks/looked fine/ok/buono"
    (r"\blooks fine\b", "sembra a posto"),
    (r"\blooks ok\b", "va bene"),
    (r"\blooked fine\b", "sembrava a posto"),
    (r"\blooks knackered\b", "sembra distrutta"),
    (r"\b's shot\b", " e' andata"),
    (r"\bcompletely worn out\b", "completamente consumata"),
    # "gomma X" -> position fixes
    (r"\bfront gomme\b", "gomme anteriori"),
    (r"\brear gomme\b", "gomme posteriori"),
    (r"\bfront gomma\b", "gomma anteriore"),
    (r"\brear gomma\b", "gomma posteriore"),
    (r"\bleft front gomma\b", "anteriore sinistra"),
    (r"\bright front gomma\b", "anteriore destra"),
    (r"\bleft rear gomma\b", "posteriore sinistra"),
    (r"\bright rear gomma\b", "posteriore destra"),
    (r"\bleft side gomme\b", "gomme del lato sinistro"),
    (r"\bright side gomme\b", "gomme del lato destro"),
    # Pressure patterns
    (r"\bpressione looks\b", "la pressione sembra"),
    (r"\bpressione looks\b", "la pressione sembra"),
    # "locking" / "wheel spin" patterns
    (r"\bfront locking\b", "bloccaggio delle anteriori"),
    (r"\brear locking\b", "bloccaggio delle posteriori"),
    (r"\bleft rear locking\b", "bloccaggio della posteriore sinistra"),
    (r"\bright rear locking\b", "bloccaggio della posteriore destra"),
    (r"\bfront right locking\b", "bloccaggio dell'anteriore destra"),
    (r"\bwheel spin\b", "pattinamento"),
    (r"\brear left wheel\b", "della posteriore sinistra"),
    (r"\brear right wheel\b", "della posteriore destra"),
    # "usura" patterns
    (r"\bsignificant usura\b", "usura significativa"),
    (r"\bsome usura\b", "un po' di usura"),
    # "X's getting hot" patterns
    (r"'s getting hot\b", " si sta scaldando"),
    (r"\bare hot\b", "sono calde"),
    (r"\bare cold\b", "sono fredde"),
    # "there's a" -> "c'e' una"
    (r"\bthere's a\b", "c'e' una"),
    (r"\bthere's some\b", "ci sono"),
    (r"\bthere's\b", "c'e'"),
    # macchina patterns
    (r"\bfaster macchina\b", "macchina piu' veloce"),
    (r"\bslower macchina\b", "macchina piu' lenta"),
    # "half-way" -> "meta'"
    (r"\bhalf-way\b", "meta'"),
    (r"\bhalf-distance\b", "meta' distanza"),
    # Common remaining
    (r"\bget ready\b", "preparati"),
    (r"\bbe careful\b", "fai attenzione"),
    (r"\btake care\b", "fai attenzione"),
    (r"\bwatch out\b", "attenzione"),
    (r"\bspeed up\b", "accelera"),
    (r"\bslow down\b", "rallenta"),
    (r"\bpitting\b", "rientrando ai box"),
    (r"\brejoining\b", "rientrando in pista"),
    (r"\bapproaching\b", "in arrivo"),
    (r"\bfighting for\b", "in lotta per"),
    (r"\bbattling for\b", "in lotta per"),
    (r"\bracing us for\b", "in lotta con noi per"),
    (r"\bclass leader\b", "leader di classe"),
    (r"\bincluding\b", "incluso"),
    (r"\boverheated\b", "surriscaldati"),
    (r"\bdisqualified\b", "squalificati"),
    (r"\bfalse start\b", "partenza anticipata"),
    (r"\bfalse-start\b", "partenza anticipata"),
    (r"\bdrive-through\b", "drive-through"),
    (r"\bstop-go\b", "stop-go"),
    (r"\bcompleted\b", "completata"),
    (r"\bserved\b", "scontata"),
    (r"\bdelete\b", "cancellare"),
    (r"\btrack limits\b", "limiti di pista"),
    (r"\bwrong way\b", "direzione sbagliata"),
    (r"\btoo slowly\b", "troppo piano"),
    (r"\bnightmare\b", "da incubo"),
    (r"\bgive up\b", "mollare"),
    (r"\bwell done\b", "ben fatto"),
    (r"\bnice and smooth\b", "fluido e preciso"),
    (r"\boverdrive\b", "forzare"),
    # "the X's" possessive pattern
    (r"\bthe pioggia's\b", "la pioggia e'"),
    (r"\bthe track temperatura's\b", "la temperatura della pista"),
    (r"\bthe carburante's\b", "il carburante"),
    (r"\bthe trasmissione's\b", "la trasmissione"),
    (r"\bthe sospensione's\b", "le sospensioni"),
    (r"\bthe macchina's\b", "la macchina"),
    (r"\bthe motore's\b", "il motore"),
    # "absolutely terrible" -> "terribile"
    (r"\babsolutely terrible\b", "terribile"),
    (r"\bproperly pissing it down\b", "sta diluviando"),
    (r"\bdecreasing\b", "sta scendendo"),
    (r"\bfalling\b", "sta calando"),
    (r"\bincreasing\b", "sta salendo"),
    (r"\brising\b", "sta aumentando"),
    # Remaining pit stop patterns
    (r"\bsiamo gonna\b", ""),
    (r"\bsiamo fixing\b", "ripariamo"),
    (r"\bchange all 4 gomme\b", "cambio tutte e 4 le gomme"),
    (r"\bchange your\b", "cambiamo le tue"),
    (r"\bchange the\b", "cambiamo le"),
    (r"\bfix the\b", "ripariamo"),
    (r"\bfix your\b", "ripariamo le tue"),
    (r"\baerodinamica\b", "aerodinamica"),
    (r"\bleave the rear\b", "lasciamo la posteriore"),
    (r"\bat the next stop\b", "alla prossima sosta"),
    (r"\bonly\b", "solo"),
    (r"\bthis time\b", "questa volta"),
    (r"\bnext giro\b", "prossimo giro"),
    # More lap time patterns
    (r"\bquickest\b", "il piu' veloce"),
    (r"\bfastest\b", "il piu' veloce"),
    (r"\bsectors\b", "settori"),
    (r"\bdown in\b", "in meno in"),
    # "non count" -> "non conta"
    (r"\bnon count\b", "non conta"),
    # "is now" -> "e' ora"
    (r"\bis now\b", "e' ora"),
    # "is clear" -> "e' libero"
    (r"\bis clear\b", "e' libero"),
    # "is ok" -> "va bene"
    (r"\bis ok\b", "va bene"),
    # "is fast/quick" -> "e' veloce"
    (r"\bis fast\b", "e' veloce"),
    (r"\bis quick\b", "e' veloce"),
    # "have gone" -> "sono finite"
    (r"\bhave gone\b", "sono finite"),
    (r"\bhave overheated\b", "si sono surriscaldati"),
    # "so far" -> "finora"
    (r"\bso far\b", "finora"),
    # "keep" patterns
    (r"\bkeep 'em coming\b", "continua cosi'"),
    (r"\bkeep it up\b", "continua cosi'"),
    # Concatenation fragments
    (r"\band \b", "e "),
    (r"\bbut \b", "ma "),
    (r"\bfor \b", "per "),
    (r"\bfrom \b", "da "),
    (r"\binto \b", "in "),
    (r"\babout \b", "circa "),
    (r"\bafter \b", "dopo "),
]


# ============================================================================
# ARTICLE FIXES: add missing articles for natural Italian
# ============================================================================

ARTICLE_FIXES: dict[str, str] = {
    "carburante scarso, potresti arrivare alla fine": "il carburante e' scarso, potresti arrivare alla fine",
    "carburante scarso, potresti dover risparmiare per arrivare alla fine": "il carburante e' scarso, potresti dover risparmiare per arrivare alla fine",
    "mezzo gallone rimasto": "e' rimasto mezzo gallone",
    "un gallone rimasto": "e' rimasto un gallone",
    "un litro rimasto": "e' rimasto un litro",
}


def has_english_words(text: str) -> bool:
    """Detect if text still has English words mixed in."""
    english_indicators = {
        "we'll", "we're", "you're", "you've", "i'm", "it's", "that's",
        "your", "the ", " is ", "are ", "was ", "were", "have ", "has ",
        "got ", "get ", "let's", "gonna", "looking", "seeing",
        "here,", "mate", "changing", "putting", "adding", "going",
        "running", "coming", "still ", "clear to", "shown",
        "stopped", "passed", "fucked", "screwed", "boogered",
        "knackered", "nicely done", "sounds like", "looks like",
        "can't hear", "i can't", "answer me", "come on,",
        "acknowledged,", "understood,", "copy that,",
        "front ", "rear ", "left side", "right side",
        "this time", "next time", "at the next",
        " no ", "not ", "won't", "don't",
        "refueling", "refuel",
        " fix ", "fixes",
        " fit ", " put ",
    }
    lower = text.lower()
    return any(w in lower for w in english_indicators)


def fix_row(subtitle: str, text_for_tts: str, audio_path: str) -> tuple[str, str, bool]:
    """Fix a single row. Returns (new_subtitle, new_text_for_tts, was_changed)."""
    original_sub = subtitle
    original_tts = text_for_tts

    # 1. Try exact fixes first (on text_for_tts)
    for old, new in EXACT_FIXES.items():
        if text_for_tts == old:
            text_for_tts = new
            subtitle = new
            break
        # Also try case-insensitive match
        if text_for_tts.lower() == old.lower():
            text_for_tts = new
            subtitle = new
            break

    # 2. Article fixes
    for old, new in ARTICLE_FIXES.items():
        if text_for_tts == old:
            text_for_tts = new
            subtitle = new
            break

    # 3. If still has English after exact fixes, try regex patterns
    if has_english_words(text_for_tts):
        for pattern, replacement in REGEX_FIXES:
            text_for_tts = re.sub(pattern, replacement, text_for_tts, flags=re.IGNORECASE)
            subtitle = re.sub(pattern, replacement, subtitle, flags=re.IGNORECASE)

        # Clean up double spaces and trailing commas
        text_for_tts = re.sub(r'\s+', ' ', text_for_tts).strip().strip(',').strip()
        subtitle = re.sub(r'\s+', ' ', subtitle).strip().strip(',').strip()

    changed = (subtitle != original_sub) or (text_for_tts != original_tts)
    return subtitle, text_for_tts, changed


def main():
    if not CSV_PATH.exists():
        print(f"ERRORE: {CSV_PATH} non trovato")
        sys.exit(1)

    # Backup
    import shutil
    shutil.copy2(CSV_PATH, BACKUP_PATH)
    print(f"Backup creato: {BACKUP_PATH}")

    # Read
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)

    print(f"Lette {len(rows)} righe")

    # Fix
    fixed_count = 0
    still_mixed = 0
    fixed_paths = []

    for i, row in enumerate(rows):
        if len(row) < 4:
            continue
        audio_path, audio_filename, subtitle, text_for_tts = row[0], row[1], row[2], row[3]

        new_sub, new_tts, changed = fix_row(subtitle, text_for_tts, audio_path)

        if changed:
            row[2] = new_sub
            row[3] = new_tts
            fixed_count += 1
            fixed_paths.append(audio_path)

        # Check if still mixed
        if has_english_words(row[3]):
            still_mixed += 1

    # Write
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"\nRisultati:")
    print(f"  Frasi corrette: {fixed_count}")
    print(f"  Ancora miste (da verificare manualmente): {still_mixed}")
    print(f"\nCSV aggiornato: {CSV_PATH}")

    # Write list of changed audio paths for selective regeneration
    changed_list = CSV_PATH.parent / "paths_to_regenerate.txt"
    unique_paths = sorted(set(fixed_paths))
    with open(changed_list, "w", encoding="utf-8") as f:
        for p in unique_paths:
            f.write(p + "\n")
    print(f"Lista percorsi da rigenerare: {changed_list} ({len(unique_paths)} percorsi unici)")


if __name__ == "__main__":
    main()
