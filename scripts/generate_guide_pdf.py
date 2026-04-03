#!/usr/bin/env python3
"""
Generate the comprehensive Italian guide PDF for CrewChief V4 - Voice Pack Marco.
Output: docs/GUIDA_COMPLETA_CREWCHIEF_ITA.pdf
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
    PageBreak, KeepTogether, Frame, PageTemplate, BaseDocTemplate,
    NextPageTemplate,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "docs")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "GUIDA_COMPLETA_CREWCHIEF_ITA.pdf")

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
style_toc_title = ParagraphStyle(
    "TOCTitle", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=22, leading=26,
    textColor=COLOR_PRIMARY, spaceAfter=18,
)
style_toc_entry = ParagraphStyle(
    "TOCEntry", parent=styles["Normal"],
    fontName="Helvetica", fontSize=13, leading=22,
    textColor=black, leftIndent=12,
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
style_bullet = ParagraphStyle(
    "Bullet", parent=style_body,
    leftIndent=20, bulletIndent=8,
    spaceAfter=3,
)
style_tip = ParagraphStyle(
    "Tip", parent=style_body,
    fontName="Helvetica-Oblique", fontSize=9.5, leading=12,
    textColor=HexColor("#1a3c6e"), leftIndent=10, rightIndent=10,
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
    """Section heading with coloured underline."""
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


def bullet(text):
    return Paragraph(f"\u2022  {text}", style_bullet)


def spacer(h=6):
    return Spacer(1, h)


def tip_box(text):
    """Grey box with a tip/note."""
    inner = Paragraph(f"<b>NOTA:</b> {text}", style_tip)
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


def cmd_table(rows, col1_title="Di'...", col2_title="Funzione"):
    """Two-column command table."""
    header = [
        Paragraph(col1_title, style_table_header),
        Paragraph(col2_title, style_table_header),
    ]
    data = [header]
    for phrase, desc in rows:
        data.append([
            Paragraph(f'<font face="Helvetica-Oblique">{phrase}</font>', style_table_cell),
            Paragraph(desc, style_table_cell),
        ])

    col_w = (PAGE_W - 2 * MARGIN - 4 * mm) / 2
    t = Table(data, colWidths=[col_w, col_w], repeatRows=1)

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
    # Alternate row colours
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), COLOR_TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))
    return t


def settings_table(rows):
    """Three-column settings table: Property, Value, Note."""
    header = [
        Paragraph("Propriet\u00e0", style_table_header),
        Paragraph("Valore", style_table_header),
        Paragraph("Note", style_table_header),
    ]
    data = [header]
    for prop, val, note in rows:
        data.append([
            Paragraph(prop, style_table_cell),
            Paragraph(f"<b>{val}</b>", style_table_cell),
            Paragraph(note, style_table_cell),
        ])

    cw = PAGE_W - 2 * MARGIN - 4 * mm
    t = Table(data, colWidths=[cw * 0.40, cw * 0.20, cw * 0.40], repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
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
    canvas.drawCentredString(PAGE_W / 2, 1.2 * cm,
                             f"Guida Completa CrewChief V4 \u2014 Voice Pack Marco  |  Pagina {doc.page}")
    canvas.restoreState()


def add_page_number_title(canvas, doc):
    """No page number on title page."""
    pass


# ---------------------------------------------------------------------------
# Build story
# ---------------------------------------------------------------------------
def build_story():
    story = []

    # -----------------------------------------------------------------------
    # PAGE 1 \u2014 Title
    # -----------------------------------------------------------------------
    story.append(Spacer(1, 5 * cm))
    story.append(HRFlowable(width="60%", thickness=3, color=COLOR_PRIMARY, spaceAfter=14))
    story.append(Paragraph("GUIDA COMPLETA", style_title_page))
    story.append(Paragraph("CREWCHIEF V4", style_title_page))
    story.append(Spacer(1, 6))
    story.append(Paragraph("VOICE PACK ITALIANO", ParagraphStyle(
        "VPI", parent=style_subtitle, fontSize=18, textColor=COLOR_ACCENT)))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="60%", thickness=1, color=COLOR_SECONDARY, spaceAfter=14))
    story.append(Paragraph("Voice Pack Marco \u2014 Ingegnere di Pista", style_subtitle))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Versione 1.0 \u2014 Aprile 2026", style_version))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "La guida definitiva per configurare e utilizzare CrewChief V4<br/>"
        "con il voice pack italiano Marco. Comandi vocali, spotter,<br/>"
        "strategia carburante, gomme, endurance e molto altro.",
        ParagraphStyle("Desc", parent=style_body, alignment=TA_CENTER, fontSize=11, leading=15,
                       textColor=COLOR_GRAY)))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # PAGE 2 \u2014 INDICE
    # -----------------------------------------------------------------------
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("INDICE", style_toc_title))
    story.append(Spacer(1, 8))

    toc_items = [
        ("1.", "Installazione e Verifica"),
        ("2.", "Comandi Vocali Italiani"),
        ("3.", "Configurazione Volante"),
        ("4.", "Nomi Curve"),
        ("5.", "Spotter"),
        ("6.", "Carburante"),
        ("7.", "Gomme"),
        ("8.", "Endurance \u2014 Le Mans Ultimate"),
        ("9.", "Penalit\u00e0 e Bandiere"),
        ("10.", "Impostazioni Consigliate"),
        ("A.", "Riferimento Rapido Comandi"),
        ("B.", "Domande Frequenti (FAQ)"),
        ("C.", "Simulatori Supportati"),
    ]
    for num, title in toc_items:
        row = Table(
            [[Paragraph(f"<b>{num}</b>", ParagraphStyle("TN", parent=style_toc_entry,
                                                         fontName="Helvetica-Bold",
                                                         textColor=COLOR_ACCENT)),
              Paragraph(title, style_toc_entry)]],
            colWidths=[1.2 * cm, 14 * cm],
        )
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(row)

    story.append(Spacer(1, 1.5 * cm))
    story.append(tip_box(
        "Questa guida \u00e8 ottimizzata per Le Mans Ultimate e iRacing, "
        "ma la maggior parte delle funzionalit\u00e0 si applica a tutti i simulatori supportati da CrewChief V4."
    ))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 1 \u2014 INSTALLAZIONE E VERIFICA
    # -----------------------------------------------------------------------
    story.extend(heading1("1. INSTALLAZIONE E VERIFICA"))
    story.append(body(
        "Dopo aver installato il voice pack Marco, \u00e8 fondamentale verificare che tutti i file siano "
        "nella posizione corretta e che CrewChief sia configurato per utilizzare la voce italiana."
    ))

    story.extend(heading2("1.1 Percorsi dei file"))
    story.append(body("Verifica che le seguenti cartelle esistano e contengano file audio (.wav):"))
    story.append(spacer(4))

    paths = [
        ("Voice pack principale", "C:\\Users\\&lt;utente&gt;\\AppData\\Local\\CrewChiefV4\\sounds\\alt\\Marco\\"),
        ("Spotter", "C:\\Users\\&lt;utente&gt;\\AppData\\Local\\CrewChiefV4\\sounds\\voice\\spotter_Marco\\"),
        ("Radio check", "C:\\Users\\&lt;utente&gt;\\AppData\\Local\\CrewChiefV4\\sounds\\voice\\radio_check_Marco\\"),
        ("Speech recognition", "C:\\Users\\&lt;utente&gt;\\AppData\\Local\\CrewChiefV4\\speech_recognition_config.txt"),
    ]
    for label, path in paths:
        story.append(bullet(f"<b>{label}:</b><br/><font face='Helvetica' size='8' color='#444444'>{path}</font>"))
    story.append(spacer(6))

    story.extend(heading2("1.2 Impostazioni CrewChief"))
    story.append(body("Apri CrewChief V4 e configura le seguenti opzioni:"))
    story.append(spacer(4))

    story.append(settings_table([
        ("Properties > General > Voice", "Marco", "Seleziona la voce dell'ingegnere"),
        ("Properties > General > Spotter", "Marco", "Seleziona la voce dello spotter"),
        ("Properties > Speech Recognition > Enable", "true", "Abilita il riconoscimento vocale"),
        ("Properties > Speech Recognition > Language", "Italian", "Lingua per i comandi vocali"),
    ]))
    story.append(spacer(8))

    story.append(tip_box(
        "Riavvia sempre CrewChief dopo ogni modifica alle impostazioni vocali. "
        "Le modifiche non hanno effetto immediato."
    ))
    story.append(spacer(8))

    story.extend(heading2("1.3 Test rapido"))
    story.append(body(
        "Per verificare che tutto funzioni correttamente, avvia CrewChief e pronuncia uno dei seguenti comandi:"
    ))
    story.append(bullet('<b>"prova radio"</b> \u2014 Marco risponder\u00e0 confermando la ricezione'))
    story.append(bullet('<b>"mi senti"</b> \u2014 alternativa al comando precedente'))
    story.append(spacer(6))
    story.append(body(
        "Se non ricevi risposta, verifica che il microfono sia selezionato correttamente in "
        "<b>Properties > Audio > Microphone device</b> e che il riconoscimento vocale sia attivo."
    ))
    story.append(spacer(6))

    story.extend(heading2("1.4 Risoluzione problemi comuni"))
    story.append(bullet(
        "<b>Nessuna risposta vocale:</b> Verifica che la voce Marco sia selezionata e che i file audio "
        "siano presenti nella cartella corretta."
    ))
    story.append(bullet(
        "<b>Comandi non riconosciuti:</b> Assicurati che la lingua sia impostata su Italian nel "
        "riconoscimento vocale di Windows e di CrewChief."
    ))
    story.append(bullet(
        "<b>Audio disturbato:</b> Controlla che non ci siano conflitti con altri software audio. "
        "Chiudi Discord, TeamSpeak o altri programmi VoIP durante il test."
    ))
    story.append(bullet(
        "<b>Spotter silenzioso:</b> Verifica che lo spotter Marco sia selezionato e che "
        "\"Enable spotter\" sia attivo nelle Properties."
    ))
    story.append(bullet(
        "<b>Ritardo nelle risposte:</b> Se Marco risponde con ritardo, verifica che il tuo sistema "
        "non sia sovraccarico. Chiudi le applicazioni in background non necessarie. CrewChief "
        "funziona meglio con almeno 8 GB di RAM liberi."
    ))
    story.append(bullet(
        "<b>Conflitto con Windows Speech Recognition:</b> Se usi Windows 10/11, verifica che il "
        "riconoscimento vocale di Windows non sia attivo contemporaneamente. Vai in Impostazioni > "
        "Privacy > Comandi vocali e disattiva \"Riconoscimento vocale online\" se causa conflitti."
    ))
    story.append(spacer(8))

    story.extend(heading2("1.5 Checklist prima della prima gara"))
    story.append(body(
        "Prima di entrare in pista per la prima volta con il voice pack Marco, segui questa checklist:"
    ))
    story.append(spacer(4))
    story.append(bullet("<b>1.</b> File audio installati nelle cartelle corrette (vedi sezione 1.1)"))
    story.append(bullet("<b>2.</b> Voce Marco selezionata come Voice e come Spotter"))
    story.append(bullet("<b>3.</b> Riconoscimento vocale abilitato con lingua Italian"))
    story.append(bullet("<b>4.</b> Microfono selezionato e testato in Properties > Audio"))
    story.append(bullet("<b>5.</b> Tasto volante assegnato per il riconoscimento vocale (vedi sezione 3)"))
    story.append(bullet("<b>6.</b> CrewChief riavviato dopo tutte le modifiche"))
    story.append(bullet("<b>7.</b> Test \"prova radio\" completato con successo"))
    story.append(bullet("<b>8.</b> Sessione di pratica di 5 minuti per familiarizzare con i comandi"))
    story.append(spacer(6))

    story.append(tip_box(
        "Si consiglia di fare almeno 10-15 minuti di pratica libera usando i comandi vocali prima "
        "di entrare in una gara online. Questo ti permetter\u00e0 di familiarizzare con la pronuncia "
        "corretta e i tempi di risposta di Marco."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 2 \u2014 COMANDI VOCALI ITALIANI
    # -----------------------------------------------------------------------
    story.extend(heading1("2. COMANDI VOCALI ITALIANI"))
    story.append(body(
        "Questa sezione elenca tutti i comandi vocali disponibili con il voice pack Marco. "
        "Pronuncia le frasi esattamente come riportate nella colonna sinistra. "
        "Puoi usare indifferentemente una qualsiasi delle varianti elencate."
    ))
    story.append(spacer(4))
    story.append(tip_box(
        "Tieni premuto il tasto assegnato al riconoscimento vocale, aspetta il beep, pronuncia il comando "
        "e rilascia il tasto. Parla a voce normale e chiara."
    ))

    # -- Stato Vettura --
    story.extend(heading2("2.1 Stato Vettura"))
    story.append(cmd_table([
        ('"come sono le gomme"', "Report completo usura e condizione gomme"),
        ('"com\'e\' l\'usura gomme"', "Alternativa per lo stato gomme"),
        ('"com\'e\' il motore" / "stato del motore"', "Condizione e temperature motore"),
        ('"come sono i freni" / "stato dei freni"', "Usura e temperature freni"),
        ('"com\'e\' il carburante" / "stato carburante"', "Livello carburante e stima giri rimanenti"),
        ('"com\'e\' la batteria" / "livello batteria"', "Stato batteria (solo vetture ibride/elettriche)"),
        ('"com\'e\' la trasmissione" / "stato del cambio"', "Condizione cambio e trasmissione"),
        ('"com\'e\' l\'aerodinamica" / "stato aerodinamica"', "Danni aerodinamici"),
        ('"come sono le sospensioni"', "Stato sospensioni e danni"),
        ('"rapporto danni" / "stato della macchina"', "Report completo di tutti i danni"),
        ('"stato completo" / "aggiornami su tutto"', "Report generale su tutto: gomme, carburante, tempi, posizione"),
    ]))

    # -- Temperature --
    story.extend(heading2("2.2 Temperature"))
    story.append(cmd_table([
        ('"temperature delle gomme"', "Temperature interne di tutte e quattro le gomme"),
        ('"come sono le temperature gomme"', "Alternativa con indicazione se troppo calde/fredde"),
        ('"temperature dei freni"', "Temperature di tutti e quattro i dischi freno"),
        ('"come sono le temperature freni"', "Alternativa con avviso se fuori range"),
        ('"temperatura del motore" / "temperature motore"', "Temperatura acqua e olio motore"),
        ('"temperatura aria"', "Temperatura ambiente attuale"),
        ('"temperatura pista"', "Temperatura superfice della pista"),
    ]))

    # -- Posizione e Distacchi --
    story.extend(heading2("2.3 Posizione e Distacchi"))
    story.append(cmd_table([
        ('"qual e\' la mia posizione" / "posizione"', "Posizione attuale in classifica"),
        ('"qual e\' il distacco davanti" / "gap davanti"', "Distacco in secondi dal pilota davanti"),
        ('"quanto ho davanti"', "Alternativa per il gap davanti"),
        ('"qual e\' il distacco dietro" / "gap dietro"', "Distacco in secondi dal pilota dietro"),
        ('"quanto ho dietro"', "Alternativa per il gap dietro"),
        ('"chi e\' davanti" / "chi mi precede"', "Nome del pilota nella posizione davanti"),
        ('"chi e\' dietro" / "chi mi segue"', "Nome del pilota nella posizione dietro"),
        ('"chi e\' in testa" / "chi comanda la gara"', "Nome del leader della gara"),
    ]))

    story.append(PageBreak())

    # -- Tempi --
    story.extend(heading2("2.4 Tempi"))
    story.append(cmd_table([
        ('"tempo ultimo giro" / "ultimo giro"', "Tempo dell'ultimo giro completato"),
        ('"miglior tempo" / "miglior giro"', "Il tuo miglior tempo nella sessione"),
        ('"giro veloce della gara"', "Il giro pi\u00f9 veloce della gara (qualsiasi pilota)"),
        ('"tempi nei settori" / "i miei settori"', "Tempi dei singoli settori dell'ultimo giro"),
        ('"com\'e\' il mio passo" / "il mio passo"', "Media tempi degli ultimi giri (race pace)"),
    ]))

    # -- Carburante --
    story.extend(heading2("2.5 Carburante"))
    story.append(cmd_table([
        ('"stato carburante" / "quanto carburante ho"', "Litri rimanenti nel serbatoio"),
        ('"consumo carburante" / "quanto consumo"', "Consumo medio per giro in litri"),
        ('"quanto carburante mi serve per finire"', "Stima litri necessari per terminare la gara"),
        ('"calcola carburante per [N] giri"', "Stima litri per un numero specifico di giri"),
        ('"calcola carburante per [N] minuti"', "Stima litri per un tempo specifico"),
        ('"calcola carburante per [N] ore"', "Stima litri per una durata in ore"),
    ]))

    # -- Strategia e Pit Stop --
    story.extend(heading2("2.6 Strategia e Pit Stop"))
    story.append(cmd_table([
        ('"devo fare una sosta"', "Verifica se hai un pit stop obbligatorio"),
        ('"ho un pit stop obbligatorio"', "Alternativa per verificare soste obbligatorie"),
        ('"dove esco se mi fermo"', "Stima posizione dopo la sosta ai box"),
        ('"stima posizioni dopo la sosta"', "Alternativa per la stima posizioni"),
        ('"cronometra questa sosta" / "test pit stop"', "Cronometra il tempo della sosta ai box"),
    ]))
    story.append(spacer(6))

    story.extend(heading3("Comandi Pit Stop specifici iRacing"))
    story.append(body(
        "I seguenti comandi funzionano solo su iRacing e controllano direttamente la schermata pit:"
    ))
    story.append(cmd_table([
        ('"pit stop cambia tutte le gomme"', "Richiedi cambio completo pneumatici"),
        ('"pit stop cambia anteriore sinistra"', "Cambia solo la gomma anteriore sinistra"),
        ('"pit stop cambia anteriore destra"', "Cambia solo la gomma anteriore destra"),
        ('"pit stop cambia posteriore sinistra"', "Cambia solo la gomma posteriore sinistra"),
        ('"pit stop cambia posteriore destra"', "Cambia solo la gomma posteriore destra"),
        ('"pit stop benzina fino alla fine"', "Rifornisci il carburante necessario per finire"),
        ('"pit stop niente gomme"', "Non cambiare le gomme alla prossima sosta"),
        ('"pit stop niente benzina"', "Non aggiungere carburante alla prossima sosta"),
    ]))

    story.append(PageBreak())

    # -- Comunicazione --
    story.extend(heading2("2.7 Comunicazione"))
    story.append(cmd_table([
        ('"stai zitto" / "silenzio"', "Marco smette di parlare temporaneamente"),
        ('"lasciami in pace"', "Modalit\u00e0 silenziosa prolungata"),
        ('"tienimi aggiornato" / "aggiornami"', "Riprende le comunicazioni normali"),
        ('"dimmi i distacchi"', "Attiva i report periodici sui distacchi"),
        ('"basta distacchi"', "Disattiva i report periodici sui distacchi"),
        ('"parlami ovunque"', "Marco parla in qualsiasi punto del circuito"),
        ('"non parlare in curva"', "Marco parla solo nei rettilinei"),
        ('"ripeti" / "cosa hai detto"', "Ripete l\'ultimo messaggio"),
        ('"dimmi di piu\'" / "piu\' informazioni"', "Fornisce dettagli aggiuntivi sull\'ultimo argomento"),
    ]))

    # -- Spotter --
    story.extend(heading2("2.8 Spotter"))
    story.append(cmd_table([
        ('"spotter attivo" / "attiva lo spotter"', "Attiva le chiamate dello spotter"),
        ('"disattiva lo spotter"', "Disattiva temporaneamente lo spotter"),
    ]))

    # -- Bandiere e Incidenti --
    story.extend(heading2("2.9 Bandiere e Incidenti"))
    story.append(cmd_table([
        ('"dimmi le bandiere gialle"', "Attiva le notifiche bandiere gialle"),
        ('"basta bandiere gialle"', "Disattiva le notifiche bandiere gialle"),
        ('"ho una penalita\'"', "Verifica se hai penalit\u00e0 pendenti"),
        ('"penalita\' scontata"', "Conferma che la penalit\u00e0 \u00e8 stata scontata"),
        ('"quanti incidenti ho"', "Numero di incidenti accumulati"),
        ('"limite incidenti"', "Quanti incidenti puoi ancora avere prima della squalifica"),
    ]))

    # -- Multiclass --
    story.extend(heading2("2.10 Multiclass"))
    story.append(cmd_table([
        ('"la macchina davanti e\' della mia classe"', "Verifica se il pilota davanti \u00e8 nella tua classe"),
        ('"che classe e\' la macchina davanti"', "Classe della vettura davanti"),
        ('"che classe e\' la macchina dietro"', "Classe della vettura dietro"),
    ]))

    story.append(PageBreak())

    # -- Varie --
    story.extend(heading2("2.11 Varie"))
    story.append(cmd_table([
        ('"quanto manca" / "quanti giri mancano"', "Giri o tempo rimanente alla fine della gara"),
        ('"che ore sono"', "Ora attuale (utile nelle gare endurance)"),
        ('"prova radio" / "mi senti"', "Test comunicazione con Marco"),
        ('"nomi delle curve"', "Elenca i nomi di tutte le curve del circuito"),
        ('"partenza lanciata"', "Informazioni sulla procedura di partenza lanciata"),
        ('"partenza da fermo"', "Informazioni sulla procedura di partenza da fermo"),
        ('"imposta sveglia alle [ora]"', "Sveglia ad un orario specifico (endurance)"),
    ]))

    story.append(spacer(10))
    story.append(tip_box(
        "Se un comando non viene riconosciuto, prova a pronunciarlo pi\u00f9 lentamente e chiaramente. "
        "Puoi anche verificare i comandi disponibili nel file speech_recognition_config.txt nella cartella di CrewChief."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 3 \u2014 CONFIGURAZIONE VOLANTE
    # -----------------------------------------------------------------------
    story.extend(heading1("3. CONFIGURAZIONE VOLANTE"))
    story.append(body(
        "Per utilizzare i comandi vocali durante la guida, \u00e8 necessario configurare un tasto "
        "sul volante per attivare il riconoscimento vocale. Questa sezione descrive la procedura "
        "per i volanti Fanatec, ma il principio \u00e8 identico per tutte le marche."
    ))

    story.extend(heading2("3.1 Assegnazione tasto \u2014 Fanatec DD1 / DD2"))
    story.append(body("Procedura di configurazione:"))
    story.append(spacer(4))
    story.append(bullet("Apri CrewChief V4 e vai in <b>Properties > Controls</b>"))
    story.append(bullet('Cerca <b>"Voice recognition button"</b>'))
    story.append(bullet("Clicca sul campo di assegnazione e premi il tasto desiderato sul volante"))
    story.append(bullet("Suggerimenti: pulsante destro del paddle shifter, o un tasto dedicato non usato nel gioco"))
    story.append(spacer(6))

    story.extend(heading2("3.2 Come usare il tasto"))
    story.append(body("Il funzionamento \u00e8 semplice:"))
    story.append(spacer(4))
    story.append(bullet("<b>1.</b> Tieni premuto il tasto sul volante"))
    story.append(bullet("<b>2.</b> Aspetta il beep di conferma"))
    story.append(bullet("<b>3.</b> Pronuncia il comando"))
    story.append(bullet("<b>4.</b> Rilascia il tasto"))
    story.append(spacer(6))

    story.extend(heading2("3.3 Modalit\u00e0 Always Listening"))
    story.append(body(
        'In alternativa al tasto, puoi attivare la modalit\u00e0 "always listening" che ascolta '
        "continuamente il microfono senza bisogno di premere un tasto:"
    ))
    story.append(spacer(4))
    story.append(settings_table([
        ("Properties > Speech Recognition > Always listening", "true",
         "Il microfono resta sempre attivo"),
    ]))
    story.append(spacer(6))
    story.append(tip_box(
        "La modalit\u00e0 Always Listening consuma pi\u00f9 risorse di sistema e potrebbe attivarsi "
        "con rumori ambientali (ventilatori, TV, altre persone). Si consiglia di usare il tasto sul "
        "volante per un'esperienza pi\u00f9 affidabile."
    ))

    story.extend(heading2("3.4 Configurazione per altri volanti"))
    story.append(body(
        "La procedura \u00e8 identica per tutti i volanti. Ecco alcuni suggerimenti specifici "
        "per le marche pi\u00f9 comuni:"
    ))
    story.append(spacer(4))

    wheel_data = [
        [Paragraph("<b>Volante</b>", style_table_header),
         Paragraph("<b>Tasto consigliato</b>", style_table_header),
         Paragraph("<b>Note</b>", style_table_header)],
        [Paragraph("Fanatec DD1/DD2", style_table_cell),
         Paragraph("Pulsante paddle destro o tasto dedicato", style_table_cell),
         Paragraph("Evita i tasti usati per DRS o pit limiter nel gioco", style_table_cell)],
        [Paragraph("Fanatec CSL DD", style_table_cell),
         Paragraph("Tasto sul rim o button module", style_table_cell),
         Paragraph("Il button module offre pi\u00f9 opzioni di tasti dedicati", style_table_cell)],
        [Paragraph("Thrustmaster T300/T500", style_table_cell),
         Paragraph("Tasto sul volante non assegnato nel gioco", style_table_cell),
         Paragraph("Verifica che il tasto non sia gi\u00e0 mappato nel simulatore", style_table_cell)],
        [Paragraph("Logitech G923/G29", style_table_cell),
         Paragraph("Tasto L3/R3 o un tasto della plancia", style_table_cell),
         Paragraph("I tasti frontali sono i pi\u00f9 accessibili durante la guida", style_table_cell)],
        [Paragraph("Simucube 2", style_table_cell),
         Paragraph("Tasto sul rim (dipende dal modello)", style_table_cell),
         Paragraph("Usa il software True Drive per verificare la mappatura", style_table_cell)],
        [Paragraph("Moza R9/R12/R16/R21", style_table_cell),
         Paragraph("Tasto sul rim GS/RS/FSR", style_table_cell),
         Paragraph("Configura prima in Moza Pit House, poi assegna in CrewChief", style_table_cell)],
    ]
    cw = PAGE_W - 2 * MARGIN - 4 * mm
    wheel_table = Table(wheel_data, colWidths=[cw * 0.28, cw * 0.35, cw * 0.37], repeatRows=1)
    wheel_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 2), (-1, 2), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 4), (-1, 4), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 6), (-1, 6), COLOR_TABLE_ALT),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(wheel_table)
    story.append(spacer(8))

    story.extend(heading2("3.5 Suggerimenti per il riconoscimento vocale"))
    story.append(bullet("Parla chiaramente, a voce normale \u2014 non serve urlare"))
    story.append(bullet("Aspetta sempre il beep prima di parlare"))
    story.append(bullet("Se non riconosce il comando, ripeti pi\u00f9 lentamente"))
    story.append(bullet("Verifica che il microfono corretto sia selezionato in <b>Properties > Audio</b>"))
    story.append(bullet("Evita microfoni con forte riduzione del rumore che possono tagliare le parole"))
    story.append(bullet(
        "Se usi un headset, assicurati che il microfono sia posizionato correttamente davanti alla bocca"
    ))
    story.append(bullet(
        "In ambienti rumorosi (cockpit con pedaliera, ventilatori, ecc.), il tasto push-to-talk "
        "\u00e8 fortemente consigliato rispetto all'always listening"
    ))
    story.append(spacer(6))

    story.extend(heading2("3.6 Configurazione microfono in Windows"))
    story.append(body(
        "Per ottenere i migliori risultati con il riconoscimento vocale, configura correttamente "
        "il microfono nelle impostazioni di Windows:"
    ))
    story.append(spacer(4))
    story.append(bullet("<b>1.</b> Apri Impostazioni > Sistema > Audio > Propriet\u00e0 dispositivo di input"))
    story.append(bullet("<b>2.</b> Imposta il volume del microfono al 75-85% (non al massimo per evitare distorsione)"))
    story.append(bullet("<b>3.</b> Disattiva i miglioramenti audio se presenti (\"Audio enhancements\" = Off)"))
    story.append(bullet("<b>4.</b> In CrewChief, seleziona lo stesso microfono in Properties > Audio > Microphone device"))
    story.append(bullet("<b>5.</b> Testa il microfono con \"prova radio\" e regola il volume se necessario"))
    story.append(spacer(6))

    story.append(tip_box(
        "Se usi cuffie con microfono integrato (es. HyperX, SteelSeries, ecc.), assicurati che "
        "Windows stia usando il microfono delle cuffie e non quello integrato nel laptop o nella webcam. "
        "Controlla nelle impostazioni audio di Windows quale dispositivo \u00e8 selezionato come predefinito."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 4 \u2014 NOMI CURVE
    # -----------------------------------------------------------------------
    story.extend(heading1("4. NOMI CURVE"))
    story.append(body(
        "CrewChief pu\u00f2 pronunciare il nome delle curve quando ti avvicini ad esse. "
        "Questa funzionalit\u00e0 \u00e8 particolarmente utile per ricevere informazioni contestuali "
        "come \"stai bloccando l'anteriore sinistra in entrata a Copse\"."
    ))

    story.extend(heading2("4.1 Attivazione"))
    story.append(settings_table([
        ("Properties > Miscellaneous > Enable corner names", "true",
         "Attiva la pronuncia dei nomi delle curve"),
    ]))
    story.append(spacer(6))

    story.extend(heading2("4.2 Funzionamento"))
    story.append(bullet("CrewChief pronuncia il nome della curva quando ti avvicini"))
    story.append(bullet("Funziona solo su circuiti supportati con mappa delle curve"))
    story.append(bullet("I nomi sono in lingua originale (es. Copse, Maggotts, Becketts, Eau Rouge)"))
    story.append(bullet("La pronuncia \u00e8 approssimata alla lingua originale"))
    story.append(spacer(6))

    story.extend(heading2("4.3 Comandi correlati"))
    story.append(cmd_table([
        ('"nomi delle curve"', "Elenca tutti i nomi delle curve del circuito attuale"),
        ('"dimmi i nomi delle curve"', "Alternativa per ascoltare l'elenco completo"),
    ]))
    story.append(spacer(6))
    story.append(tip_box(
        "I nomi delle curve vengono utilizzati anche nei messaggi sulle temperature e l'usura gomme. "
        "Ad esempio: \"stai surriscaldando l'anteriore destra a Maggotts\". "
        "Si consiglia di attivare sempre questa opzione."
    ))
    story.append(spacer(8))

    story.extend(heading2("4.4 Esempi di circuiti supportati"))
    story.append(body(
        "Ecco alcuni esempi di circuiti con i nomi delle curve pi\u00f9 iconiche. "
        "CrewChief user\u00e0 questi nomi nei messaggi contestuali:"
    ))
    story.append(spacer(4))

    circuit_data = [
        [Paragraph("<b>Circuito</b>", style_table_header),
         Paragraph("<b>Curve principali</b>", style_table_header)],
        [Paragraph("Le Mans (Circuit de la Sarthe)", style_table_cell),
         Paragraph("Dunlop, Tertre Rouge, Mulsanne, Indianapolis, Arnage, Porsche Curves, Ford Chicane", style_table_cell)],
        [Paragraph("Silverstone", style_table_cell),
         Paragraph("Copse, Maggotts, Becketts, Stowe, Club, Abbey, Village, The Loop", style_table_cell)],
        [Paragraph("Spa-Francorchamps", style_table_cell),
         Paragraph("La Source, Eau Rouge, Raidillon, Les Combes, Pouhon, Stavelot, Bus Stop", style_table_cell)],
        [Paragraph("Monza", style_table_cell),
         Paragraph("Variante del Rettifilo, Curva Grande, Variante della Roggia, Lesmo 1, Lesmo 2, Ascari, Parabolica", style_table_cell)],
        [Paragraph("N\u00fcrburgring GP", style_table_cell),
         Paragraph("Turn 1 (Yokohama), Mercedes Arena, Dunlop, Schumacher S, Veedol Chicane", style_table_cell)],
        [Paragraph("Daytona", style_table_cell),
         Paragraph("Turn 1, International Horseshoe, Bus Stop Chicane, NASCAR Turn 1-4", style_table_cell)],
    ]
    cw = PAGE_W - 2 * MARGIN - 4 * mm
    circuit_table = Table(circuit_data, colWidths=[cw * 0.30, cw * 0.70], repeatRows=1)
    circuit_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 2), (-1, 2), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 4), (-1, 4), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 6), (-1, 6), COLOR_TABLE_ALT),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(circuit_table)
    story.append(spacer(6))
    story.append(body(
        "L'elenco completo dei circuiti supportati dipende dalla versione di CrewChief e dal simulatore "
        "in uso. Per i circuiti non ancora mappati, CrewChief utilizzer\u00e0 numeri progressivi "
        "(\"curva 1\", \"curva 2\", ecc.) al posto dei nomi."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 5 \u2014 SPOTTER
    # -----------------------------------------------------------------------
    story.extend(heading1("5. SPOTTER"))
    story.append(body(
        "Lo spotter \u00e8 la funzionalit\u00e0 pi\u00f9 importante di CrewChief per la sicurezza in pista. "
        "Ti avvisa in tempo reale della presenza di altre vetture affiancate a te, "
        "permettendoti di evitare contatti."
    ))

    story.extend(heading2("5.1 Configurazione"))
    story.append(settings_table([
        ("Properties > General > Spotter", "Marco", "Voce italiana per lo spotter"),
        ("Properties > Spotter > Enable spotter", "true", "Attiva lo spotter"),
        ("Properties > Spotter > Car length multiplier", "1.2",
         "Alza a 1.2 per chiamate pi\u00f9 sensibili (default 1.0)"),
        ("Properties > Spotter > Enable 3-wide calls", "true",
         "Abilita le chiamate quando siete in tre affiancati"),
    ]))
    story.append(spacer(8))

    story.extend(heading2("5.2 Chiamate dello spotter"))
    story.append(body(
        "Lo spotter utilizza chiamate brevi e immediate per comunicare la posizione "
        "delle altre vetture. Ecco le chiamate che sentirai:"
    ))
    story.append(spacer(4))
    story.append(cmd_table([
        ('"lato sinistro" / "alla tua sinistra"', "Una macchina \u00e8 affiancata a sinistra"),
        ('"alla tua destra" / "lato destro"', "Una macchina \u00e8 affiancata a destra"),
        ('"e\' ancora li\'"', "La macchina \u00e8 ancora affiancata, non spostarti"),
        ('"libero a sinistra"', "Il lato sinistro \u00e8 ora libero"),
        ('"libero a destra"', "Il lato destro \u00e8 ora libero"),
        ('"libero tutto intorno"', "Nessuna macchina affiancata, sei libero"),
        ('"tre in parallelo"', "Tre macchine affiancate \u2014 massima attenzione!"),
        ('"libero all\'interno"', "Il lato interno della curva \u00e8 libero"),
        ('"libero all\'esterno"', "Il lato esterno della curva \u00e8 libero"),
    ], col1_title="Marco dice...", col2_title="Significato"))

    story.append(spacer(8))
    story.append(tip_box(
        "Lo spotter \u00e8 particolarmente critico nelle gare multiclass dove vetture di classi diverse "
        "hanno velocit\u00e0 molto differenti. Alza il car length multiplier a 1.2-1.3 per avere chiamate "
        "pi\u00f9 anticipate e precauzionali."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 6 \u2014 CARBURANTE
    # -----------------------------------------------------------------------
    story.extend(heading1("6. CARBURANTE"))
    story.append(body(
        "La gestione del carburante \u00e8 fondamentale in ogni gara, specialmente nelle endurance. "
        "CrewChief monitora costantemente il consumo e fornisce stime precise."
    ))

    story.extend(heading2("6.1 Calcolo automatico"))
    story.append(bullet("CrewChief calcola il consumo medio dopo <b>3-4 giri</b> completati"))
    story.append(bullet("Gli avvisi automatici scattano quando il carburante \u00e8 basso"))
    story.append(bullet('Di\' <b>"quanto carburante mi serve per finire"</b> per la stima dei litri necessari'))
    story.append(bullet('Di\' <b>"calcola carburante per trenta giri"</b> per stime personalizzate'))
    story.append(spacer(6))

    story.extend(heading2("6.2 Avvisi carburante"))
    story.append(body("Marco ti avviser\u00e0 con messaggi crescenti di urgenza:"))
    story.append(spacer(4))
    story.append(cmd_table([
        ('"Carburante per [N] giri"', "Informazione periodica sulla stima giri rimanenti"),
        ('"Carburante basso"', "Hai carburante per circa 2-3 giri"),
        ('"Carburante critico"', "Meno di 1 giro di carburante, fermati subito!"),
        ('"Finestra rifornimento aperta"', "Puoi effettuare il pit stop per il rifornimento"),
    ], col1_title="Marco dice...", col2_title="Significato"))

    story.extend(heading2("6.3 Auto-refuelling (iRacing)"))
    story.append(body(
        "Su iRacing, CrewChief pu\u00f2 calcolare e inserire automaticamente la quantit\u00e0 "
        "di carburante necessaria quando entri ai box:"
    ))
    story.append(spacer(4))
    story.append(settings_table([
        ("Fuel > Enable fuel messages", "true", "Abilita tutti i messaggi carburante"),
        ("Fuel > Auto-fill fuel on pit entry", "true", "Calcola automaticamente il rifornimento"),
        ("Fuel > Fuel use window size", "3", "Numero di giri per calcolare la media del consumo"),
        ("Fuel > Fuel warning threshold", "2.0", "Giri di margine per l'avviso carburante basso"),
    ]))

    story.append(spacer(8))
    story.append(tip_box(
        "Nelle gare endurance, \u00e8 consigliabile alzare il Fuel warning threshold a 3.0 per avere "
        "pi\u00f9 tempo di pianificare la sosta. In gare sprint, il valore di default 2.0 \u00e8 sufficiente."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 7 \u2014 GOMME
    # -----------------------------------------------------------------------
    story.extend(heading1("7. GOMME"))
    story.append(body(
        "Il monitoraggio delle gomme \u00e8 essenziale per mantenere le prestazioni durante tutta "
        "la gara. CrewChief monitora temperature, usura e comportamento in pista."
    ))

    story.extend(heading2("7.1 Temperature"))
    story.append(body("Le soglie di temperatura variano per mescola, ma in generale:"))
    story.append(spacer(4))

    temp_data = [
        [Paragraph("<b>Condizione</b>", style_table_header),
         Paragraph("<b>Temperatura</b>", style_table_header),
         Paragraph("<b>Azione</b>", style_table_header)],
        [Paragraph("Troppo fredde", style_table_cell),
         Paragraph("&lt; 70\u00b0C", style_table_cell),
         Paragraph("Spingi di pi\u00f9 per scaldare le gomme, zig-zag nei rettilinei", style_table_cell)],
        [Paragraph("Ideali", style_table_cell),
         Paragraph("80\u00b0C \u2013 100\u00b0C", style_table_cell),
         Paragraph("Range ottimale, massimo grip disponibile", style_table_cell)],
        [Paragraph("Calde", style_table_cell),
         Paragraph("100\u00b0C \u2013 110\u00b0C", style_table_cell),
         Paragraph("Attenzione, riduci l'aggressivit\u00e0 in curva", style_table_cell)],
        [Paragraph("Troppo calde", style_table_cell),
         Paragraph("&gt; 110\u00b0C", style_table_cell),
         Paragraph("Rischio di blistering, rallenta e gestisci le gomme", style_table_cell)],
    ]
    cw = PAGE_W - 2 * MARGIN - 4 * mm
    temp_table = Table(temp_data, colWidths=[cw * 0.25, cw * 0.25, cw * 0.50], repeatRows=1)
    temp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 2), (-1, 2), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 4), (-1, 4), COLOR_TABLE_ALT),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(temp_table)
    story.append(spacer(8))

    story.extend(heading2("7.2 Degrado e usura"))
    story.append(bullet('Di\' <b>"come sono le gomme"</b> per il report completo dell\'usura'))
    story.append(bullet('Di\' <b>"quanto durano queste gomme"</b> per la stima dei giri rimanenti'))
    story.append(bullet("Marco avviser\u00e0 automaticamente quando una gomma \u00e8 \"distrutta\" o \"consumata\""))
    story.append(bullet("Gli avvisi includono quale gomma specifica ha problemi (es. \"anteriore destra consumata\")"))
    story.append(spacer(6))

    story.extend(heading2("7.3 Bloccaggio e pattinamento"))
    story.append(body(
        "Lo spotter e l'ingegnere collaborano per segnalare problemi di guida legati alle gomme:"
    ))
    story.append(spacer(4))
    story.append(bullet("Avviso se <b>blocchi le anteriori</b> in frenata: "
                        "\"stai bloccando l'anteriore sinistra in entrata a [curva]\""))
    story.append(bullet("Avviso se <b>pattini le posteriori</b> in accelerazione"))
    story.append(bullet("Questi avvisi sono contestuali alla curva se i nomi curve sono attivi"))
    story.append(spacer(6))

    story.extend(heading2("7.4 Properties consigliate"))
    story.append(settings_table([
        ("Tyres > Enable tyre messages", "true", "Abilita tutti i messaggi gomme"),
        ("Tyres > Report tyre temps every N laps", "5", "Frequenza report temperature automatici"),
        ("Tyres > Warn when tyre temp exceeds", "personalizzabile",
         "Soglia personalizzata per avviso temperatura"),
    ]))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 8 \u2014 ENDURANCE \u2014 LE MANS ULTIMATE
    # -----------------------------------------------------------------------
    story.extend(heading1("8. ENDURANCE \u2014 LE MANS ULTIMATE"))
    story.append(body(
        "Le gare endurance su Le Mans Ultimate presentano sfide uniche: stint lunghi, "
        "cambio pilota, classi multiple, condizioni meteo variabili e transizioni giorno/notte. "
        "CrewChief con il voice pack Marco \u00e8 il compagno ideale per queste gare."
    ))

    story.extend(heading2("8.1 Stint e cambio pilota"))
    story.append(body("Marco ti avviser\u00e0 del tempo rimanente nello stint con messaggi progressivi:"))
    story.append(spacer(4))
    story.append(bullet("<b>15 minuti rimanenti:</b> \"quindici minuti alla fine dello stint\""))
    story.append(bullet("<b>5 minuti rimanenti:</b> \"cinque minuti, preparati per la sosta\""))
    story.append(bullet("<b>2 minuti rimanenti:</b> \"due minuti, rientra ai box\""))
    story.append(bullet("<b>Cambio pilota:</b> \"cambio pilota tra cinque minuti\""))
    story.append(spacer(4))
    story.append(body(
        "CrewChief tiene conto del tempo minimo di sosta obbligatoria e ti avvisa "
        "se la finestra per il pit stop \u00e8 aperta."
    ))

    story.extend(heading2("8.2 Classi multiple"))
    story.append(body(
        "Le Mans Ultimate presenta tre classi principali con velocit\u00e0 molto diverse. "
        "CrewChief gestisce attivamente le interazioni tra classi:"
    ))
    story.append(spacer(4))

    class_data = [
        [Paragraph("<b>Classe</b>", style_table_header),
         Paragraph("<b>Tipo</b>", style_table_header),
         Paragraph("<b>Velocit\u00e0 indicativa</b>", style_table_header)],
        [Paragraph("Hypercar", style_table_cell),
         Paragraph("Prototipo top class", style_table_cell),
         Paragraph("La pi\u00f9 veloce, circa 3:20-3:30 a Le Mans", style_table_cell)],
        [Paragraph("LMP2", style_table_cell),
         Paragraph("Prototipo", style_table_cell),
         Paragraph("5-8 secondi pi\u00f9 lenta per giro", style_table_cell)],
        [Paragraph("LMGT3", style_table_cell),
         Paragraph("Gran Turismo", style_table_cell),
         Paragraph("15-20 secondi pi\u00f9 lenta per giro", style_table_cell)],
    ]
    cw = PAGE_W - 2 * MARGIN - 4 * mm
    class_table = Table(class_data, colWidths=[cw * 0.25, cw * 0.30, cw * 0.45], repeatRows=1)
    class_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 2), (-1, 2), COLOR_TABLE_ALT),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(class_table)
    story.append(spacer(6))

    story.append(body("Avvisi multiclass di Marco:"))
    story.append(bullet("<b>\"macchine pi\u00f9 veloci in arrivo\"</b> \u2014 una classe superiore si sta avvicinando"))
    story.append(bullet("<b>\"stai raggiungendo le macchine pi\u00f9 lente\"</b> \u2014 stai per doppiare una classe inferiore"))
    story.append(bullet("Lo spotter indica la classe quando vieni doppiato o doppi"))
    story.append(spacer(6))

    story.extend(heading2("8.3 Meteo"))
    story.append(body(
        "Le Mans Ultimate include condizioni meteo dinamiche. Marco ti tiene aggiornato "
        "in tempo reale:"
    ))
    story.append(spacer(4))
    story.append(bullet("<b>\"sta iniziando a piovere\"</b> \u2014 prime gocce, considera il cambio gomme"))
    story.append(bullet("<b>\"ha smesso di piovere\"</b> \u2014 la pioggia si \u00e8 fermata"))
    story.append(bullet("<b>\"pioggia intensa\"</b> \u2014 condizioni pericolose, massima prudenza"))
    story.append(bullet('Di\' <b>"temperatura aria"</b> o <b>"temperatura pista"</b> per monitorare le condizioni'))
    story.append(spacer(6))

    story.extend(heading2("8.4 Guida notturna"))
    story.append(body(
        "Durante le fasi notturne delle gare endurance, i fari sono obbligatori. "
        "Marco ti avviser\u00e0 se necessario:"
    ))
    story.append(spacer(4))
    story.append(bullet("<b>\"i fari sono obbligatori, accendili\"</b> \u2014 attiva i fari per evitare penalit\u00e0"))
    story.append(bullet("Penalit\u00e0 automatica per guida senza fari nelle fasi notturne"))
    story.append(spacer(6))

    story.extend(heading2("8.5 Properties LMU"))
    story.append(settings_table([
        ("Multiclass > Enable multiclass messages", "true",
         "Abilita avvisi su classi diverse"),
        ("Multiclass > Warn about faster class", "true",
         "Avviso quando classi pi\u00f9 veloci si avvicinano"),
        ("Multiclass > Warn about slower class", "true",
         "Avviso quando raggiungi classi pi\u00f9 lente"),
        ("Conditions > Enable weather messages", "true",
         "Avvisi meteo in tempo reale"),
        ("Conditions > Enable track temp", "true",
         "Report temperatura pista"),
        ("Mandatory pit stops > Enable", "true",
         "Avvisi soste obbligatorie e finestre pit"),
        ("Mandatory pit stops > Remind on window open", "true",
         "Notifica quando la finestra pit si apre"),
    ]))

    story.append(spacer(8))
    story.append(tip_box(
        "Per le gare 24 ore, imposta una sveglia con il comando \"imposta sveglia alle [ora]\" "
        "per essere avvisato quando \u00e8 il tuo turno di guida. Marco ti sveglier\u00e0 "
        "con un avviso sonoro."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 9 \u2014 PENALITA E BANDIERE
    # -----------------------------------------------------------------------
    story.extend(heading1("9. PENALIT\u00c0 E BANDIERE"))
    story.append(body(
        "CrewChief ti mantiene informato su tutte le bandiere esposte dal direttore di gara "
        "e su eventuali penalit\u00e0 ricevute. \u00c8 fondamentale reagire prontamente "
        "per evitare sanzioni pi\u00f9 gravi."
    ))

    story.extend(heading2("9.1 Bandiere"))
    story.append(spacer(4))

    flag_data = [
        [Paragraph("<b>Bandiera</b>", style_table_header),
         Paragraph("<b>Marco dice...</b>", style_table_header),
         Paragraph("<b>Cosa fare</b>", style_table_header)],
        [Paragraph("Gialla", style_table_cell),
         Paragraph("\"bandiera gialla attenzione\"", style_table_cell),
         Paragraph("Rallenta, incidente in pista, divieto di sorpasso nella zona", style_table_cell)],
        [Paragraph("Doppia gialla", style_table_cell),
         Paragraph("\"doppie gialle attenzione\"", style_table_cell),
         Paragraph("Grande pericolo, rallenta significativamente, preparati a fermarti", style_table_cell)],
        [Paragraph("Verde", style_table_cell),
         Paragraph("\"bandiera verde tutto libero\"", style_table_cell),
         Paragraph("Incidente risolto, riprendi il ritmo normale", style_table_cell)],
        [Paragraph("Blu", style_table_cell),
         Paragraph("\"bandiera blu, lascia passare\"", style_table_cell),
         Paragraph("Stai per essere doppiato, lascia passare la macchina pi\u00f9 veloce", style_table_cell)],
        [Paragraph("Nera", style_table_cell),
         Paragraph("\"bandiera nera\"", style_table_cell),
         Paragraph("Penalit\u00e0 grave, rientra ai box immediatamente", style_table_cell)],
        [Paragraph("Bianca", style_table_cell),
         Paragraph("\"bandiera bianca\"", style_table_cell),
         Paragraph("Ultimo giro o veicolo lento in pista", style_table_cell)],
    ]
    cw = PAGE_W - 2 * MARGIN - 4 * mm
    flag_table = Table(flag_data, colWidths=[cw * 0.18, cw * 0.37, cw * 0.45], repeatRows=1)
    flag_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 2), (-1, 2), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 4), (-1, 4), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 6), (-1, 6), COLOR_TABLE_ALT),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(flag_table)
    story.append(spacer(8))

    story.extend(heading2("9.2 Penalit\u00e0"))
    story.append(body("Marco ti avviser\u00e0 immediatamente in caso di penalit\u00e0:"))
    story.append(spacer(4))
    story.append(cmd_table([
        ('"limiti pista, resta tra le linee"', "Taglio pista \u2014 avviso track limits"),
        ('"abbiamo preso un drive-through"', "Penalit\u00e0 drive-through da scontare ai box"),
        ('"abbiamo preso uno stop-go"', "Penalit\u00e0 stop-go (pi\u00f9 grave del drive-through)"),
        ('"stai attento, un\'altra collisione e saremo squalificati"', "Sei vicino al limite incidenti"),
    ], col1_title="Marco dice...", col2_title="Significato"))
    story.append(spacer(6))

    story.extend(heading2("9.3 Safety Car"))
    story.append(body("Durante le fasi di Safety Car, Marco fornisce le seguenti informazioni:"))
    story.append(spacer(4))
    story.append(bullet("<b>\"safety car in pista\"</b> \u2014 la safety car \u00e8 stata dispiegata"))
    story.append(bullet("<b>\"preparati per bandiera verde\"</b> \u2014 la safety car sta per rientrare"))
    story.append(bullet("<b>\"divieto di sorpasso\"</b> \u2014 non puoi sorpassare durante la safety car"))
    story.append(spacer(6))

    story.extend(heading2("9.4 Properties"))
    story.append(settings_table([
        ("Penalties > Enable penalty messages", "true", "Abilita messaggi penalit\u00e0"),
        ("Penalties > Enable cut track warnings", "true", "Avvisi taglio pista / track limits"),
        ("Flags > Enable yellow flag messages", "true", "Notifiche bandiere gialle"),
        ("Flags > Enable blue flag messages", "true", "Notifiche bandiere blu"),
    ]))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 10 \u2014 IMPOSTAZIONI CONSIGLIATE
    # -----------------------------------------------------------------------
    story.extend(heading1("10. IMPOSTAZIONI CONSIGLIATE"))
    story.append(body(
        "Questa sezione riassume tutte le impostazioni consigliate per ottenere "
        "la migliore esperienza con il voice pack Marco su Le Mans Ultimate. "
        "Puoi adattare questi valori alle tue preferenze personali."
    ))

    story.extend(heading2("10.1 General"))
    story.append(settings_table([
        ("Voice", "Marco", "Voce dell'ingegnere di pista"),
        ("Spotter", "Marco", "Voce dello spotter"),
        ("Game", "Le Mans Ultimate / rFactor 2", "Seleziona il simulatore in uso"),
    ]))

    story.extend(heading2("10.2 Speech Recognition"))
    story.append(settings_table([
        ("Enable speech recognition", "true", "Abilita i comandi vocali"),
        ("Language", "Italian", "Lingua per il riconoscimento vocale"),
        ("Always listening", "false", "Usa il tasto sul volante (pi\u00f9 affidabile)"),
        ("Voice recognition button", "[assegna]", "Tasto sul volante per parlare"),
    ]))

    story.extend(heading2("10.3 Spotter"))
    story.append(settings_table([
        ("Enable spotter", "true", "Attiva le chiamate dello spotter"),
        ("Car length multiplier", "1.2", "Sensibilit\u00e0 pi\u00f9 alta del default (1.0)"),
        ("Enable 3-wide calls", "true", "Chiamate quando in tre affiancati"),
    ]))

    story.extend(heading2("10.4 Fuel"))
    story.append(settings_table([
        ("Enable fuel messages", "true", "Abilita avvisi carburante"),
        ("Fuel use window size", "3", "Giri per calcolo media consumo"),
        ("Fuel warning threshold", "2.0", "Giri di margine per avviso (3.0 per endurance)"),
        ("Auto-fill fuel on pit entry", "true", "Solo iRacing: rifornimento automatico"),
    ]))

    story.extend(heading2("10.5 Tyres"))
    story.append(settings_table([
        ("Enable tyre messages", "true", "Abilita avvisi gomme"),
        ("Report tyre temps every N laps", "5", "Frequenza report automatico temperature"),
    ]))

    story.extend(heading2("10.6 Timing"))
    story.append(settings_table([
        ("Enable gap reports", "true", "Abilita report sui distacchi"),
        ("Report interval", "every lap", "Frequenza report distacchi"),
    ]))

    story.append(PageBreak())

    story.extend(heading2("10.7 Multiclass"))
    story.append(settings_table([
        ("Enable multiclass messages", "true", "Abilita messaggi multiclass"),
        ("Warn about faster class", "true", "Avviso classi pi\u00f9 veloci in arrivo"),
        ("Warn about slower class", "true", "Avviso classi pi\u00f9 lente che raggiungi"),
    ]))

    story.extend(heading2("10.8 Conditions"))
    story.append(settings_table([
        ("Enable weather messages", "true", "Avvisi cambiamento meteo"),
        ("Enable track temp messages", "true", "Report temperatura pista"),
    ]))

    story.extend(heading2("10.9 Penalties"))
    story.append(settings_table([
        ("Enable penalty messages", "true", "Messaggi su tutte le penalit\u00e0"),
        ("Enable cut track warnings", "true", "Avvisi taglio pista"),
        ("Severity", "all", "Notifica tutte le penalit\u00e0, anche le minori"),
    ]))

    story.extend(heading2("10.10 Mandatory Pit Stops"))
    story.append(settings_table([
        ("Enable mandatory stop messages", "true", "Avvisi soste obbligatorie"),
        ("Remind on window open", "true", "Notifica apertura finestra pit"),
    ]))

    story.append(spacer(1.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=COLOR_SECONDARY, spaceAfter=12))

    story.append(tip_box(
        "Queste impostazioni sono un punto di partenza consigliato. Ogni pilota ha preferenze diverse: "
        "alcuni preferiscono meno comunicazioni per concentrarsi, altri vogliono essere aggiornati su tutto. "
        "Sperimenta e trova il tuo equilibrio ideale."
    ))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # APPENDIX A \u2014 QUICK REFERENCE COMANDI
    # -----------------------------------------------------------------------
    story.extend(heading1("APPENDICE A \u2014 RIFERIMENTO RAPIDO COMANDI"))
    story.append(body(
        "Tabella riassuntiva dei comandi pi\u00f9 usati durante una gara. "
        "Tieni questa pagina a portata di mano durante le prime sessioni."
    ))
    story.append(spacer(6))

    story.extend(heading2("Comandi essenziali per la gara"))
    story.append(cmd_table([
        ('"prova radio"', "Test comunicazione"),
        ('"posizione"', "Posizione in classifica"),
        ('"gap davanti"', "Distacco dal pilota davanti"),
        ('"gap dietro"', "Distacco dal pilota dietro"),
        ('"stato carburante"', "Livello carburante"),
        ('"come sono le gomme"', "Stato gomme"),
        ('"ultimo giro"', "Tempo ultimo giro"),
        ('"quanto manca"', "Giri/tempo rimanente"),
        ('"stato completo"', "Report generale"),
        ('"ripeti"', "Ripete l'ultimo messaggio"),
    ]))
    story.append(spacer(8))

    story.extend(heading2("Comandi per gestire Marco"))
    story.append(cmd_table([
        ('"stai zitto"', "Silenzia Marco"),
        ('"aggiornami"', "Riattiva le comunicazioni"),
        ('"non parlare in curva"', "Parla solo nei rettilinei"),
        ('"parlami ovunque"', "Parla in qualsiasi punto"),
        ('"dimmi i distacchi"', "Attiva report distacchi"),
        ('"basta distacchi"', "Disattiva report distacchi"),
    ]))
    story.append(spacer(8))

    story.extend(heading2("Comandi endurance"))
    story.append(cmd_table([
        ('"quanto carburante mi serve per finire"', "Stima litri per finire"),
        ('"devo fare una sosta"', "Verifica soste obbligatorie"),
        ('"dove esco se mi fermo"', "Stima posizione dopo pit"),
        ('"che ore sono"', "Ora attuale"),
        ('"temperatura aria"', "Temperatura ambiente"),
        ('"la macchina davanti e\' della mia classe"', "Verifica classe"),
    ]))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # APPENDIX B \u2014 FAQ
    # -----------------------------------------------------------------------
    story.extend(heading1("APPENDICE B \u2014 DOMANDE FREQUENTI (FAQ)"))
    story.append(spacer(6))

    faqs = [
        ("Marco non risponde ai comandi vocali. Cosa faccio?",
         "Verifica che il riconoscimento vocale sia abilitato in Properties > Speech Recognition, "
         "che la lingua sia impostata su Italian, che il microfono sia correttamente selezionato "
         "in Properties > Audio, e che tu stia tenendo premuto il tasto vocale prima di parlare. "
         "Riavvia CrewChief dopo ogni modifica."),
        ("Posso usare Marco e lo spotter Jim contemporaneamente?",
         "S\u00ec, puoi usare voci diverse per l'ingegnere e lo spotter. In Properties > General, "
         "puoi selezionare Marco come Voice e Jim (o qualsiasi altra voce) come Spotter, o viceversa. "
         "Tuttavia, per un'esperienza completamente in italiano, si consiglia di usare Marco per entrambi."),
        ("I comandi vocali funzionano anche durante le replay?",
         "S\u00ec, puoi usare i comandi vocali anche durante le replay. Questo \u00e8 utile per "
         "verificare informazioni sulla gara appena conclusa, come tempi, posizioni e statistiche."),
        ("CrewChief funziona con tutti i simulatori?",
         "CrewChief V4 supporta molti simulatori tra cui Le Mans Ultimate, iRacing, rFactor 2, "
         "Assetto Corsa Competizione, Automobilista 2, Project Cars 2, F1, e altri. "
         "Il voice pack Marco funziona con tutti i simulatori supportati, ma alcune funzionalit\u00e0 "
         "(come i comandi pit stop specifici) sono disponibili solo su determinati giochi."),
        ("Come faccio ad aggiornare il voice pack Marco?",
         "Scarica la nuova versione del voice pack e sovrascrivi i file nella cartella "
         "AppData\\Local\\CrewChiefV4\\sounds\\alt\\Marco\\. Riavvia CrewChief dopo l'aggiornamento. "
         "Le tue impostazioni personali non verranno modificate."),
        ("Posso personalizzare la frequenza dei messaggi?",
         "S\u00ec, molte opzioni sono configurabili nelle Properties di CrewChief. Ad esempio, puoi "
         "modificare la frequenza dei report temperature gomme, dei report distacchi, degli avvisi "
         "carburante e molto altro. Consulta la sezione 10 per le impostazioni consigliate."),
        ("Marco parla troppo durante la gara. Come lo silenzio parzialmente?",
         "Puoi usare il comando \"non parlare in curva\" per limitare i messaggi ai rettilinei. "
         "Puoi anche disattivare categorie specifiche di messaggi nelle Properties, ad esempio "
         "disattivando i report distacchi automatici o riducendo la frequenza dei report gomme."),
        ("Lo spotter \u00e8 in ritardo nelle chiamate. Come posso migliorarlo?",
         "Verifica che il tuo sistema non sia sovraccarico (CPU e RAM). Chiudi le applicazioni "
         "non necessarie. Se il problema persiste, prova a ridurre il car length multiplier a 1.0. "
         "Lo spotter dipende anche dalla frequenza di aggiornamento dei dati del simulatore."),
        ("Posso usare CrewChief con VR?",
         "Assolutamente s\u00ec. CrewChief \u00e8 particolarmente utile in VR perch\u00e9 non puoi "
         "guardare app esterne durante la guida. I comandi vocali ti permettono di ottenere tutte "
         "le informazioni di cui hai bisogno senza togliere le mani dal volante o lo sguardo dalla pista."),
        ("Come funziona il calcolo del carburante nelle gare a tempo?",
         "Nelle gare a tempo (es. 24 ore), CrewChief calcola il consumo medio per giro e stima "
         "quanti giri puoi completare con il carburante rimanente. Usa il comando \"calcola carburante "
         "per due ore\" per ottenere stime basate sul tempo rimanente. Il calcolo diventa pi\u00f9 preciso "
         "dopo 3-4 giri completati."),
    ]

    for q, a in faqs:
        story.append(Paragraph(f"<b>D: {q}</b>", ParagraphStyle(
            "FAQ_Q", parent=style_body, fontName="Helvetica-Bold", fontSize=10,
            leading=13, spaceBefore=8, spaceAfter=2, textColor=COLOR_PRIMARY)))
        story.append(Paragraph(f"R: {a}", ParagraphStyle(
            "FAQ_A", parent=style_body, fontSize=9.5, leading=12.5,
            leftIndent=10, spaceAfter=6, textColor=HexColor("#333333"))))

    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # APPENDIX C \u2014 SIMULATORI SUPPORTATI
    # -----------------------------------------------------------------------
    story.extend(heading1("APPENDICE C \u2014 SIMULATORI SUPPORTATI"))
    story.append(body(
        "Il voice pack Marco per CrewChief V4 funziona con tutti i simulatori supportati. "
        "Ecco una panoramica delle funzionalit\u00e0 disponibili per ciascun simulatore:"
    ))
    story.append(spacer(6))

    sim_data = [
        [Paragraph("<b>Simulatore</b>", style_table_header),
         Paragraph("<b>Comandi vocali</b>", style_table_header),
         Paragraph("<b>Pit commands</b>", style_table_header),
         Paragraph("<b>Multiclass</b>", style_table_header)],
        [Paragraph("Le Mans Ultimate", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Base", style_table_cell),
         Paragraph("Completo", style_table_cell)],
        [Paragraph("iRacing", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Completo", style_table_cell)],
        [Paragraph("rFactor 2", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Base", style_table_cell),
         Paragraph("Completo", style_table_cell)],
        [Paragraph("Assetto Corsa Competizione", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Non disponibili", style_table_cell),
         Paragraph("Parziale", style_table_cell)],
        [Paragraph("Automobilista 2", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Base", style_table_cell),
         Paragraph("Parziale", style_table_cell)],
        [Paragraph("F1 2024/2025", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Non disponibili", style_table_cell),
         Paragraph("N/A", style_table_cell)],
        [Paragraph("Project Cars 2", style_table_cell),
         Paragraph("Completi", style_table_cell),
         Paragraph("Non disponibili", style_table_cell),
         Paragraph("Parziale", style_table_cell)],
    ]
    cw = PAGE_W - 2 * MARGIN - 4 * mm
    sim_table = Table(sim_data, colWidths=[cw * 0.35, cw * 0.20, cw * 0.22, cw * 0.23], repeatRows=1)
    sim_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 2), (-1, 2), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 4), (-1, 4), COLOR_TABLE_ALT),
        ("BACKGROUND", (0, 6), (-1, 6), COLOR_TABLE_ALT),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(sim_table)
    story.append(spacer(8))

    story.append(body(
        "<b>Legenda:</b><br/>"
        "\u2022 <b>Completi:</b> tutte le funzionalit\u00e0 disponibili<br/>"
        "\u2022 <b>Base:</b> funzionalit\u00e0 di base disponibili, senza controllo diretto della schermata pit<br/>"
        "\u2022 <b>Parziale:</b> supporto limitato, dipende dalla versione del simulatore<br/>"
        "\u2022 <b>Non disponibili:</b> il simulatore non espone le API necessarie"
    ))
    story.append(spacer(10))

    story.extend(heading2("Note sulla compatibilit\u00e0"))
    story.append(bullet(
        "<b>Le Mans Ultimate / rFactor 2:</b> Stesso motore (Madness Engine), supporto eccellente. "
        "Le funzionalit\u00e0 multiclass sono particolarmente avanzate."
    ))
    story.append(bullet(
        "<b>iRacing:</b> Il supporto pi\u00f9 completo grazie alle API avanzate di iRacing. "
        "I comandi pit stop controllano direttamente la schermata pit del gioco."
    ))
    story.append(bullet(
        "<b>Assetto Corsa Competizione:</b> Ottimo supporto per i comandi vocali e lo spotter. "
        "I comandi pit non sono disponibili perch\u00e9 ACC gestisce la strategia internamente."
    ))
    story.append(bullet(
        "<b>Automobilista 2:</b> Basato su Madness Engine come rFactor 2, buon supporto generale. "
        "Alcune funzionalit\u00e0 dipendono dalla versione del gioco."
    ))

    story.append(spacer(1.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARY, spaceAfter=14))

    # -- Final page note --
    story.append(Paragraph(
        "Buona guida con Marco, il tuo ingegnere di pista italiano!",
        ParagraphStyle("Final", parent=style_body, alignment=TA_CENTER,
                       fontSize=13, leading=16, textColor=COLOR_PRIMARY,
                       fontName="Helvetica-Bold")
    ))
    story.append(spacer(6))
    story.append(Paragraph(
        "Voice Pack Marco per CrewChief V4 \u2014 Versione 1.0 \u2014 Aprile 2026",
        ParagraphStyle("FinalSub", parent=style_body, alignment=TA_CENTER,
                       fontSize=9, textColor=COLOR_GRAY)
    ))
    story.append(spacer(4))
    story.append(Paragraph(
        "Questa guida \u00e8 stata creata per il progetto CrewChief ITA Voice Pack.<br/>"
        "Per aggiornamenti e nuove versioni, visita il repository del progetto.",
        ParagraphStyle("FinalNote", parent=style_body, alignment=TA_CENTER,
                       fontSize=8, leading=11, textColor=COLOR_GRAY)
    ))

    return story


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=2 * cm,
        title="Guida Completa CrewChief V4 - Voice Pack Marco",
        author="CrewChief ITA Voice Pack Project",
        subject="Guida all'uso del voice pack italiano Marco per CrewChief V4",
    )

    story = build_story()
    doc.build(story, onFirstPage=add_page_number_title, onLaterPages=add_page_number)

    print(f"PDF generato con successo: {OUTPUT_FILE}")
    print(f"Dimensione: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
