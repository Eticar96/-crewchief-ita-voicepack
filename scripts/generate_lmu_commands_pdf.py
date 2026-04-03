#!/usr/bin/env python3
"""
Generate the LMU (Le Mans Ultimate) voice commands PDF for CrewChief V4 - Voice Pack Marco.
Output: docs/COMANDI_VOCALI_LMU.pdf

This PDF covers ONLY commands compatible with Le Mans Ultimate / rFactor 2.
iRacing-specific commands (pit macros, iRating, license class, SOF) are excluded.
"""

import os
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "docs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "COMANDI_VOCALI_LMU.pdf")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
COLOR_PRIMARY = HexColor("#1a3c6e")
COLOR_SECONDARY = HexColor("#2d6bb4")
COLOR_ACCENT = HexColor("#e8712b")
COLOR_LIGHT_BG = HexColor("#f0f4f8")
COLOR_TIP_BG = HexColor("#e6eef7")
COLOR_TIP_BORDER = HexColor("#2d6bb4")
COLOR_WARNING_BG = HexColor("#fff3e0")
COLOR_WARNING_BORDER = HexColor("#e8712b")
COLOR_TABLE_HEADER = HexColor("#1a3c6e")
COLOR_TABLE_ALT = HexColor("#f5f7fa")
COLOR_GRAY = HexColor("#666666")

PAGE_W, PAGE_H = A4
MARGIN = 2.0 * cm

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

style_title_page = ParagraphStyle(
    "TitlePage", parent=styles["Title"],
    fontName="Helvetica-Bold", fontSize=28, leading=34,
    textColor=COLOR_PRIMARY, alignment=TA_CENTER, spaceAfter=12,
)
style_subtitle = ParagraphStyle(
    "SubTitle", parent=styles["Title"],
    fontName="Helvetica", fontSize=16, leading=20,
    textColor=COLOR_SECONDARY, alignment=TA_CENTER, spaceAfter=6,
)
style_version = ParagraphStyle(
    "Version", parent=styles["Normal"],
    fontName="Helvetica", fontSize=12, leading=14,
    textColor=COLOR_GRAY, alignment=TA_CENTER, spaceAfter=6,
)
style_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=20, leading=24,
    textColor=COLOR_PRIMARY, spaceBefore=0, spaceAfter=10,
    borderWidth=0, borderColor=COLOR_PRIMARY,
)
style_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontName="Helvetica-Bold", fontSize=14, leading=18,
    textColor=COLOR_SECONDARY, spaceBefore=14, spaceAfter=6,
)
style_h3 = ParagraphStyle(
    "H3", parent=styles["Heading3"],
    fontName="Helvetica-Bold", fontSize=11, leading=14,
    textColor=COLOR_ACCENT, spaceBefore=10, spaceAfter=4,
)
style_body = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontName="Helvetica", fontSize=10, leading=13,
    textColor=black, alignment=TA_JUSTIFY, spaceAfter=6,
)
style_tip = ParagraphStyle(
    "Tip", parent=style_body,
    fontName="Helvetica-Oblique", fontSize=9.5, leading=12,
    textColor=HexColor("#1a3c6e"), leftIndent=10, rightIndent=10,
    spaceBefore=2, spaceAfter=2,
)
style_warning = ParagraphStyle(
    "Warning", parent=style_body,
    fontName="Helvetica", fontSize=9.5, leading=12,
    textColor=HexColor("#bf360c"), leftIndent=10, rightIndent=10,
    spaceBefore=2, spaceAfter=2,
)
style_table_header = ParagraphStyle(
    "TH", parent=styles["Normal"],
    fontName="Helvetica-Bold", fontSize=9.5, leading=12,
    textColor=white, alignment=TA_LEFT,
)
style_table_cell = ParagraphStyle(
    "TD", parent=styles["Normal"],
    fontName="Helvetica", fontSize=9, leading=11.5,
    textColor=black,
)
style_footer = ParagraphStyle(
    "Footer", parent=styles["Normal"],
    fontName="Helvetica", fontSize=8, textColor=COLOR_GRAY,
    alignment=TA_CENTER,
)

# ---------------------------------------------------------------------------
# Helper flowables
# ---------------------------------------------------------------------------

def heading1(text):
    return [
        Paragraph(text, style_h1),
        HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=8),
    ]


def heading2(text):
    return [Paragraph(text, style_h2)]


def heading3(text):
    return [Paragraph(text, style_h3)]


def body(text):
    return Paragraph(text, style_body)


def spacer(h=6):
    return Spacer(1, h)


def tip_box(text):
    inner = Paragraph(f"<b>SUGGERIMENTO:</b> {text}", style_tip)
    t = Table([[inner]], colWidths=[PAGE_W - 2 * MARGIN - 8 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_TIP_BG),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_TIP_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def warning_box(text):
    inner = Paragraph(f"<b>ATTENZIONE:</b> {text}", style_warning)
    t = Table([[inner]], colWidths=[PAGE_W - 2 * MARGIN - 8 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_WARNING_BG),
        ("BOX", (0, 0), (-1, -1), 2, COLOR_WARNING_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def cmd_table(rows):
    """Three-column command table: Frase da dire | Cosa fa / Risposta | Note."""
    header = [
        Paragraph("Frase da dire", style_table_header),
        Paragraph("Cosa fa / Risposta", style_table_header),
        Paragraph("Note", style_table_header),
    ]
    data = [header]
    for phrase, desc, note in rows:
        data.append([
            Paragraph(f'<font face="Helvetica-Oblique">&laquo;{phrase}&raquo;</font>', style_table_cell),
            Paragraph(desc, style_table_cell),
            Paragraph(note, style_table_cell),
        ])

    cw = PAGE_W - 2 * MARGIN - 4 * mm
    t = Table(data, colWidths=[cw * 0.35, cw * 0.40, cw * 0.25], repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), COLOR_TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


# ---------------------------------------------------------------------------
# Page number callback
# ---------------------------------------------------------------------------
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(COLOR_GRAY)
    canvas.drawCentredString(
        PAGE_W / 2, 1.2 * cm,
        f"Comandi Vocali LMU - Voice Pack Marco  |  Pagina {doc.page}"
    )
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Build document
# ---------------------------------------------------------------------------
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="Comandi Vocali Italiani - Le Mans Ultimate",
        author="CrewChief V4 - Voice Pack Marco",
    )

    story = []

    # ===== TITLE PAGE =====
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("COMANDI VOCALI ITALIANI", style_title_page))
    story.append(Paragraph("LE MANS ULTIMATE", style_title_page))
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph("Voice Pack Marco per CrewChief V4", style_subtitle))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("Compatibile con LMU / rFactor 2", style_version))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Guida di riferimento rapido a tutti i comandi vocali italiani "
        "utilizzabili con Le Mans Ultimate tramite CrewChief V4 e il Voice Pack Marco.",
        ParagraphStyle("Intro", parent=style_body, alignment=TA_CENTER, fontSize=11, leading=14),
    ))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "I comandi specifici di iRacing (pit macros, iRating, licenza, SOF) "
        "sono stati esclusi da questo documento.",
        ParagraphStyle("Disclaimer", parent=style_body, alignment=TA_CENTER,
                       fontSize=9, textColor=COLOR_GRAY),
    ))

    story.append(PageBreak())

    # =======================================================================
    # CATEGORY 1: COMANDI CHE INTERAGISCONO CON LMU
    # =======================================================================
    story.extend(heading1("1. Comandi che interagiscono con LMU"))

    story.append(warning_box(
        "A differenza di iRacing, Le Mans Ultimate <b>non permette</b> a CrewChief di "
        "controllare direttamente la strategia pit stop (carburante, gomme, riparazioni). "
        "Tutti i comandi PIT_STOP_* (cambia gomme, aggiungi carburante, ecc.) sono "
        "<b>esclusivi di iRacing</b> e NON funzionano su LMU. "
        "Il giocatore deve impostare manualmente carburante e gomme nel menu pit di LMU."
    ))
    story.append(spacer(8))

    story.append(body(
        "Su LMU, i comandi che effettivamente modificano il comportamento del gioco "
        "o di CrewChief durante la sessione sono molto limitati. Ecco quelli disponibili:"
    ))
    story.append(spacer(4))

    story.extend(heading2("Giro di formazione"))
    story.append(cmd_table([
        ("questo e' il giro di formazione",
         "Attiva la modalita' giro di formazione manuale in CrewChief",
         "Varianti: giro di formazione / partenza lanciata"),
        ("partenza da fermo",
         "Disattiva la modalita' giro di formazione",
         "Variante: niente giro di formazione"),
    ]))
    story.append(spacer(6))

    story.extend(heading2("Note di passo (Pace Notes)"))
    story.append(cmd_table([
        ("inizia le note di passo",
         "Avvia la riproduzione audio delle note di passo per il circuito",
         "Variante: avvia note di passo"),
        ("ferma le note di passo",
         "Interrompe la riproduzione delle note di passo",
         "Variante: stop note di passo"),
    ]))
    story.append(spacer(6))

    story.append(tip_box(
        "Le note di passo (pace notes) sono file audio pre-registrati che descrivono "
        "curva per curva il tracciato. Devono essere configurate preventivamente in CrewChief."
    ))

    story.append(PageBreak())

    # =======================================================================
    # CATEGORY 2: COMANDI INFORMATIVI
    # =======================================================================
    story.extend(heading1("2. Comandi informativi (Marco legge la telemetria)"))
    story.append(body(
        "Questa e' la categoria piu' ampia. CrewChief legge i dati telemetrici di LMU "
        "tramite la shared memory del plugin rFactor 2 e Marco vi comunica le informazioni "
        "richieste in italiano."
    ))
    story.append(spacer(4))

    # --- Stato Vettura ---
    story.extend(heading2("Stato Vettura"))
    story.append(cmd_table([
        ("come sono le gomme",
         "Marco dice la % di usura di ogni gomma",
         "Varianti: com'e' l'usura gomme / stato usura gomme"),
        ("com'e' la trasmissione",
         "Stato della trasmissione / cambio",
         "Varianti: com'e' il cambio / stato del cambio"),
        ("com'e' l'aerodinamica",
         "Stato aerodinamica e carrozzeria",
         "Variante: com'e' la carrozzeria"),
        ("com'e' il motore",
         "Stato del motore",
         "Varianti: stato del motore / come va il motore"),
        ("come sono le sospensioni",
         "Stato delle sospensioni",
         "Variante: stato sospensioni"),
        ("come sono i freni",
         "Stato dei freni",
         "Varianti: stato dei freni / come vanno i freni"),
        ("com'e' il carburante",
         "Livello carburante attuale",
         "Varianti: stato carburante / come va la benzina"),
        ("com'e' il mio passo",
         "Confronto ritmo con il leader",
         "Variante: come va il mio ritmo"),
        ("rapporto danni",
         "Danni a motore, aero, sospensioni",
         "Varianti: com'e' la macchina / stato danni"),
        ("stato della macchina",
         "Report completo dello stato vettura",
         "Variante: stato vettura"),
        ("aggiornamento completo",
         "Tutto insieme: posizione, gomme, carburante, danni...",
         "Varianti: stato completo / aggiornami su tutto"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "Il comando 'aggiornamento completo' e' ideale durante i rettilinei lunghi, "
        "ad esempio il rettilineo Mulsanne a Le Mans. Marco vi dara' un report esaustivo."
    ))

    # --- Temperature ---
    story.extend(heading2("Temperature"))
    story.append(cmd_table([
        ("come sono le temperature gomme",
         "Temperatura interna/esterna di ogni gomma",
         "Variante: temperature delle gomme"),
        ("come sono le temperature freni",
         "Temperatura dei freni",
         "Variante: temperature dei freni"),
        ("come sono le temperature motore",
         "Temperatura acqua e olio del motore",
         "Variante: temperatura del motore"),
        ("temperatura aria",
         "Temperatura dell'aria in gradi C",
         "Variante: qual e' la temperatura dell'aria"),
        ("temperatura pista",
         "Temperatura della pista in gradi C",
         "Variante: qual e' la temperatura della pista"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "Monitorare le temperature gomme e' fondamentale nelle gare endurance di LMU. "
        "Temperature troppo alte o basse influiscono drasticamente sulla prestazione."
    ))

    # --- Carburante ---
    story.extend(heading2("Carburante"))
    story.append(cmd_table([
        ("quanto carburante ho",
         "Litri di carburante rimanenti nel serbatoio",
         "Varianti: qual e' il mio livello carburante / livello benzina"),
        ("consumo carburante",
         "Consumo medio in litri per giro",
         "Varianti: qual e' il mio consumo / quanto consumo"),
        ("quanto carburante mi serve per finire",
         "Stima dei litri necessari per finire la gara",
         "Variante: quanta benzina per finire la gara"),
        ("calcola carburante per venti giri",
         "Stima dei litri necessari per N giri (o minuti/ore)",
         "Servono 3-4 giri di dati. Es: calcola carburante per un'ora"),
    ]))
    story.append(spacer(4))

    story.append(warning_box(
        "Il comando 'calcola carburante per...' su LMU <b>calcola e comunica</b> "
        "la quantita' necessaria, ma <b>NON riempie automaticamente</b> il serbatoio. "
        "Dovete inserire manualmente il valore nel menu pit di LMU."
    ))

    # --- Gomme ---
    story.extend(heading2("Gomme"))
    story.append(cmd_table([
        ("che gomme ho",
         "Tipo di mescola attualmente montata",
         "Varianti: su che gomma sono / che mescola ho montato"),
        ("quanto durano queste gomme",
         "Stima dei giri rimanenti con le gomme attuali",
         "Variante: per quanto reggono le gomme / durata gomme"),
        ("confronta le mescole",
         "Differenza di passo tra le diverse mescole disponibili",
         "Varianti: differenze tra le mescole / confronta le gomme"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "In LMU le classi Hypercar e LMP2 usano spesso gomme diverse. "
        "Confrontare le mescole vi aiuta a pianificare la strategia sosta."
    ))

    # --- Posizione e Classifica ---
    story.extend(heading2("Posizione e Classifica"))
    story.append(cmd_table([
        ("posizione",
         "Marco dice la vostra posizione, es. 'sei in P5'",
         "Varianti: qual e' la mia posizione / in che posizione sono"),
        ("gap davanti",
         "Distacco in secondi da chi vi precede in classifica",
         "Varianti: qual e' il distacco davanti / quanto ho davanti"),
        ("gap dietro",
         "Distacco in secondi da chi vi segue in classifica",
         "Varianti: qual e' il distacco dietro / quanto ho dietro"),
        ("chi e' davanti",
         "Nome del pilota che vi precede in classifica",
         "Varianti: chi mi precede in classifica / chi ho davanti"),
        ("chi e' dietro",
         "Nome del pilota che vi segue in classifica",
         "Varianti: chi mi segue in classifica / chi ho dietro"),
        ("chi ho davanti in pista",
         "Chi vi precede fisicamente in pista (anche se doppiato)",
         "Variante: chi mi precede in pista"),
        ("chi ho dietro in pista",
         "Chi vi segue fisicamente in pista",
         "Variante: chi mi segue in pista"),
        ("chi e' in testa",
         "Nome del leader della gara",
         "Varianti: chi comanda la gara / chi guida la gara"),
        ("dove sono piu' veloce",
         "Settore o curva dove guadagnate rispetto all'avversario",
         "Varianti: dove posso attaccare / dove devo attaccare"),
        ("dove sono piu' lento",
         "Settore o curva dove perdete",
         "Varianti: dove devo difendermi / dove mi attacca"),
    ]))

    story.append(PageBreak())

    # --- Tempi ---
    story.extend(heading2("Tempi"))
    story.append(cmd_table([
        ("ultimo giro",
         "Tempo dell'ultimo giro completato",
         "Varianti: qual e' il mio ultimo giro / tempo ultimo giro"),
        ("miglior tempo",
         "Il vostro miglior tempo personale della sessione",
         "Variante: qual e' il mio miglior giro"),
        ("giro veloce della gara",
         "Il miglior tempo assoluto in gara (qualsiasi pilota)",
         "Variante: qual e' il giro piu' veloce"),
        ("tempi nei settori",
         "Tempi S1, S2, S3 dell'ultimo giro",
         "Variante: quali sono i miei tempi settore"),
        ("ultimo settore",
         "Tempo dell'ultimo settore attraversato",
         "Variante: qual e' il mio ultimo tempo settore"),
    ]))
    story.append(spacer(6))

    # --- Multiclass ---
    story.extend(heading2("Multiclass (fondamentale per LMU!)"))
    story.append(body(
        "Le gare LMU sono quasi sempre multiclasse (Hypercar, LMP2, LMGT3). "
        "Questi comandi sono essenziali per gestire il traffico e capire "
        "chi state lottando nella vostra classe."
    ))
    story.append(cmd_table([
        ("la macchina davanti e' della mia classe",
         "Marco risponde si o no",
         "Variante: quello davanti e' della mia classe"),
        ("la macchina dietro e' della mia classe",
         "Marco risponde si o no",
         "Variante: quello dietro e' della mia classe"),
        ("che classe e' la macchina davanti",
         "Marco dice la classe: Hypercar / LMP2 / LMGT3",
         "Variante: di che classe e' quello davanti"),
        ("che classe e' la macchina dietro",
         "Marco dice la classe dell'auto dietro di voi",
         "Variante: di che classe e' quello dietro"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "In LMU multiclasse, sapere se chi avete davanti e' della vostra classe "
        "fa la differenza tra un sorpasso necessario e uno inutile (e rischioso)."
    ))

    # --- Gara ---
    story.extend(heading2("Gara"))
    story.append(cmd_table([
        ("quanto manca",
         "Giri o tempo rimanente alla fine della gara",
         "Variante: quanti giri mancano / quanto manca alla fine"),
        ("ho una penalita'",
         "Marco dice se avete una penalita' e di che tipo",
         "Variante: sono penalizzato"),
        ("penalita' scontata",
         "Conferma se la penalita' e' stata scontata",
         "Variante: ho scontato la penalita'"),
        ("devo fare una sosta",
         "Indica se c'e' una sosta obbligatoria da completare",
         "Varianti: devo rientrare ai box / ho una sosta obbligatoria"),
        ("quanti incidenti ho",
         "Conteggio dei punti incidente accumulati",
         "Variante: qual e' il mio conteggio incidenti"),
        ("limite incidenti",
         "Limite di punti incidente per la sessione",
         "Variante: qual e' il limite incidenti"),
        ("stato della sessione",
         "Informazioni generali sulla sessione in corso",
         "Variante: stato gara"),
        ("che ore sono",
         "Ora attuale (orologio reale)",
         "Variante: che ora e' / dimmi l'ora"),
    ]))

    # --- Avversari ---
    story.extend(heading2("Avversari (comandi dinamici con nomi pilota)"))
    story.append(body(
        "Questi comandi si combinano con il nome del pilota avversario. "
        "CrewChief riconosce i nomi dei piloti in sessione. "
        "Sostituite [nome] con il cognome reale del pilota."
    ))
    story.append(cmd_table([
        ("dov'e' [nome]",
         "Posizione e distacco del pilota indicato",
         "Es: dov'e' Verstappen"),
        ("qual e' di [nome] ultimo giro",
         "Tempo dell'ultimo giro del pilota indicato",
         "Usa 'di' come possessivo"),
        ("qual e' di [nome] miglior giro",
         "Miglior tempo del pilota indicato",
         "Usa 'di' come possessivo"),
        ("che gomme ha [nome] montate",
         "Mescola attualmente usata dal pilota indicato",
         "Variante: che gomma ha [nome] montate"),
        ("chi e' in posizione [N]",
         "Nome del pilota in quella posizione di classifica",
         "Es: chi e' in posizione cinque"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "Per i numeri di posizione, usate le parole italiane: "
        "'uno', 'due', 'tre', 'quattro', 'cinque', ecc. "
        "CrewChief non riconosce i numeri come cifre parlate."
    ))

    # --- Pit Stop Info ---
    story.extend(heading2("Informazioni Pit Stop"))
    story.append(cmd_table([
        ("dove esco se mi fermo",
         "Stima della posizione in cui rientrereste dopo una sosta",
         "Varianti: stima posizioni dopo la sosta / cosa succede se mi fermo"),
        ("cronometra questa sosta",
         "Cronometra il tempo del vostro pit stop (pratica)",
         "Varianti: prova pit stop / test pit stop"),
        ("il mio box e' occupato",
         "Marco dice se la vostra piazzola pit e' libera o occupata",
         "Variante: la mia piazzola e' libera / e' libero il mio box"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "Il comando 'dove esco se mi fermo' e' preziosissimo nelle gare endurance di LMU "
        "per decidere quando effettuare la sosta strategica."
    ))

    # --- Altro ---
    story.extend(heading2("Altro"))
    story.append(cmd_table([
        ("nomi delle curve",
         "Marco elenca i nomi di tutte le curve del circuito",
         "Varianti: dimmi i nomi delle curve / elenca le curve"),
        ("mi senti",
         "Marco conferma che la comunicazione radio funziona",
         "Varianti: prova radio / mi ricevi"),
        ("dimmi di piu'",
         "Marco espande l'ultimo messaggio con piu' dettagli",
         "Varianti: piu' informazioni / piu' dettagli / chiarisci"),
        ("ripeti",
         "Marco ripete l'ultimo messaggio",
         "Varianti: ripeti l'ultimo messaggio / cosa hai detto"),
        ("sto bene",
         "Risposta dopo un incidente, Marco conferma",
         "Varianti: tutto ok / va bene / ok / si sto bene"),
    ]))

    story.append(PageBreak())

    # =======================================================================
    # CATEGORY 3: COMANDI DI GESTIONE CREWCHIEF
    # =======================================================================
    story.extend(heading1("3. Comandi di gestione CrewChief"))
    story.append(body(
        "Questi comandi non leggono telemetria e non interagiscono con LMU. "
        "Controllano il comportamento di CrewChief stesso: cosa vi dice, quando, e come."
    ))
    story.append(spacer(4))

    story.extend(heading2("Volume e comunicazione"))
    story.append(cmd_table([
        ("stai zitto",
         "Marco smette di parlare (silenzio radio)",
         "Varianti: silenzio / so quello che faccio / lasciami in pace / parla meno"),
        ("tienimi aggiornato",
         "Marco riprende a parlare con gli aggiornamenti automatici",
         "Varianti: tienimi informato / aggiornami"),
    ]))
    story.append(spacer(6))

    story.extend(heading2("Report automatici"))
    story.append(cmd_table([
        ("dimmi i distacchi",
         "Attiva il report automatico dei distacchi ogni giro",
         "Varianti: dimmi i gap / dammi i distacchi / distacchi ogni giro"),
        ("basta distacchi",
         "Disattiva il report automatico dei distacchi",
         "Varianti: non dirmi i distacchi / non dirmi i gap / basta gap"),
        ("dimmi le bandiere gialle",
         "Attiva la segnalazione delle bandiere gialle",
         "Varianti: dammi gli aggiornamenti incidenti / segnalami le gialle"),
        ("basta bandiere gialle",
         "Disattiva la segnalazione delle bandiere gialle",
         "Varianti: non dirmi le gialle / basta aggiornamenti incidenti"),
    ]))
    story.append(spacer(6))

    story.extend(heading2("Quando e dove parlare"))
    story.append(cmd_table([
        ("parlami ovunque",
         "Marco vi parla in qualsiasi punto della pista",
         "Variante: messaggi in qualsiasi punto"),
        ("non parlare in curva",
         "Marco rimane in silenzio durante curve e frenate",
         "Varianti: niente messaggi in curva / non parlare in frenata"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "Il comando 'non parlare in curva' e' molto utile sui circuiti tecnici "
        "come Monza variante Ascari o le chicane di Le Mans, dove serve massima concentrazione."
    ))
    story.append(spacer(6))

    story.extend(heading2("Spotter"))
    story.append(cmd_table([
        ("spotter attivo",
         "Attiva lo spotter (avvisi di auto affiancate)",
         "Varianti: attiva lo spotter / inizia a spottare"),
        ("disattiva lo spotter",
         "Disattiva lo spotter",
         "Variante: spotter disattivo"),
    ]))
    story.append(spacer(6))

    story.extend(heading2("Sveglia"))
    story.append(cmd_table([
        ("imposta sveglia alle [ora]",
         "Marco vi sveglia all'ora indicata",
         "Variante: svegliami alle [ora]. Usare 'di mattina' / 'di pomeriggio'"),
        ("cancella sveglia",
         "Rimuove la sveglia impostata",
         "Variante: cancella le sveglie"),
    ]))
    story.append(spacer(4))

    story.append(tip_box(
        "La sveglia e' utilissima durante le sessioni endurance notturne di LMU. "
        "Potete impostarla per ricordarvi il prossimo stint o cambio pilota."
    ))

    # ===== FINAL NOTE =====
    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECONDARY, spaceAfter=10))
    story.append(body(
        "<b>Nota finale:</b> Tutti i comandi elencati in questo documento sono stati verificati "
        "come compatibili con Le Mans Ultimate (basato su rFactor 2). I comandi esclusivi "
        "di iRacing (controllo pit stop, iRating, classe licenza, SOF) sono stati intenzionalmente "
        "esclusi. Per la lista completa dei comandi (inclusi quelli iRacing), consultate la "
        "Guida Completa CrewChief ITA."
    ))

    # ===== BUILD =====
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF generato con successo: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_pdf()
