#!/usr/bin/env python3
"""
install_voicepack.py — Installa un voice pack generato in CrewChief V4.

Copia i file audio nella struttura corretta di CrewChief, creando un backup
del pack esistente prima dell'installazione. Verifica l'integrità dei file WAV.

Uso:
    python install_voicepack.py --voice Marco
    python install_voicepack.py --voice Marco --dry-run
    python install_voicepack.py --voice Marco --crewchief-dir "D:\\CrewChiefV4"
"""

from __future__ import annotations

import argparse
import getpass
import logging
import os
import shutil
import struct
import sys
import wave
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------

REQUIRED_SAMPLE_RATE = 22050
REQUIRED_CHANNELS = 1
REQUIRED_SAMPLE_WIDTH = 2  # 16-bit = 2 byte

logger = logging.getLogger("install_voicepack")


# ---------------------------------------------------------------------------
# Dataclass per i risultati
# ---------------------------------------------------------------------------


@dataclass
class InstallResult:
    """Risultato dell'installazione di un voice pack."""

    files_copied: int = 0
    files_skipped: int = 0
    files_invalid: int = 0
    total_size_bytes: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Funzioni di utilità
# ---------------------------------------------------------------------------


def _setup_logging(verbose: bool = False) -> None:
    """Configura il logging con output strutturato."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s | %(levelname)-7s | %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")


def get_default_crewchief_dir() -> Path:
    """Restituisce il percorso predefinito della cartella dati di CrewChief V4.

    Il percorso è:  C:\\Users\\<USERNAME>\\AppData\\Local\\CrewChiefV4
    """
    username = getpass.getuser()
    return Path(f"C:/Users/{username}/AppData/Local/CrewChiefV4")


def detect_crewchief_dir() -> Path | None:
    """Cerca automaticamente la cartella dati di CrewChief V4.

    Controlla prima il percorso predefinito; se non esiste, cerca nella
    variabile d'ambiente LOCALAPPDATA.

    Returns:
        Il percorso trovato oppure None.
    """
    # Tentativo 1: percorso predefinito
    default = get_default_crewchief_dir()
    if default.is_dir():
        return default

    # Tentativo 2: tramite LOCALAPPDATA
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        alt = Path(local_appdata) / "CrewChiefV4"
        if alt.is_dir():
            return alt

    return None


def validate_wav_file(filepath: Path) -> tuple[bool, str]:
    """Verifica che un file WAV rispetti il formato richiesto da CrewChief.

    Formato richiesto: 22050 Hz, 16-bit PCM, mono.

    Args:
        filepath: percorso del file WAV da verificare.

    Returns:
        Tupla (valido, messaggio). Se valido è False, il messaggio descrive
        l'errore riscontrato.
    """
    if not filepath.exists():
        return False, f"File non trovato: {filepath}"

    if filepath.stat().st_size == 0:
        return False, f"File vuoto: {filepath}"

    try:
        with wave.open(str(filepath), "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()

            problems: list[str] = []

            if framerate != REQUIRED_SAMPLE_RATE:
                problems.append(
                    f"sample rate {framerate} Hz (richiesto {REQUIRED_SAMPLE_RATE} Hz)"
                )
            if sample_width != REQUIRED_SAMPLE_WIDTH:
                bit_depth = sample_width * 8
                problems.append(
                    f"bit depth {bit_depth}-bit (richiesto {REQUIRED_SAMPLE_WIDTH * 8}-bit)"
                )
            if n_channels != REQUIRED_CHANNELS:
                problems.append(
                    f"{n_channels} canali (richiesto mono)"
                )

            if problems:
                return False, f"Formato errato in {filepath.name}: {'; '.join(problems)}"

            return True, "OK"

    except wave.Error as exc:
        return False, f"Errore nella lettura del WAV {filepath.name}: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Errore imprevisto con {filepath.name}: {exc}"


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


def create_backup(
    crewchief_dir: Path,
    voice_name: str,
    *,
    dry_run: bool = False,
) -> Path | None:
    """Crea un backup ZIP dei file esistenti per la voce indicata.

    Il backup include le cartelle alt/<voice>, spotter_<voice> e
    radio_check_<voice>, se presenti.

    Args:
        crewchief_dir: cartella radice di CrewChief.
        voice_name: nome della voce.
        dry_run: se True, non crea il backup ma mostra cosa farebbe.

    Returns:
        Il percorso del file ZIP creato, oppure None se non c'era nulla
        da salvare (o in modalità dry-run).
    """
    dirs_to_backup: list[Path] = []

    alt_dir = crewchief_dir / "sounds" / "alt" / voice_name
    spotter_dir = crewchief_dir / "sounds" / "voice" / f"spotter_{voice_name}"
    radio_dir = crewchief_dir / "sounds" / "voice" / f"radio_check_{voice_name}"

    for d in (alt_dir, spotter_dir, radio_dir):
        if d.is_dir() and any(d.iterdir()):
            dirs_to_backup.append(d)

    if not dirs_to_backup:
        logger.info("Nessun file esistente da salvare per la voce '%s'.", voice_name)
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{voice_name}_{timestamp}.zip"
    backup_path = crewchief_dir / "backups" / backup_name

    if dry_run:
        logger.info("[DRY-RUN] Creerei backup in: %s", backup_path)
        for d in dirs_to_backup:
            n_files = sum(1 for _ in d.rglob("*") if _.is_file())
            logger.info("[DRY-RUN]   - %s (%d file)", d.relative_to(crewchief_dir), n_files)
        return None

    backup_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Creazione backup in: %s", backup_path)
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in dirs_to_backup:
            for file in d.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(crewchief_dir)
                    zf.write(file, arcname)

    size_mb = backup_path.stat().st_size / (1024 * 1024)
    logger.info("Backup completato: %.2f MB", size_mb)
    return backup_path


# ---------------------------------------------------------------------------
# Installazione
# ---------------------------------------------------------------------------


def _classify_source_files(
    source_dir: Path, voice_name: str
) -> tuple[list[Path], list[Path], list[Path]]:
    """Classifica i file sorgente in main, spotter e radio_check.

    La classificazione avviene in base alla struttura delle sotto-cartelle
    nella directory sorgente.

    Returns:
        Tuple con (main_files, spotter_files, radio_check_files).
    """
    main_files: list[Path] = []
    spotter_files: list[Path] = []
    radio_check_files: list[Path] = []

    for wav in source_dir.rglob("*.wav"):
        rel = wav.relative_to(source_dir)
        parts_lower = [p.lower() for p in rel.parts]

        # Classifica in base alla struttura del percorso relativo.
        #
        # Struttura sorgente (sotto output/<Voice>/):
        #   voice/spotter_<Voice>/...     -> spotter
        #   voice/radio_check_<Voice>/... -> radio_check
        #   voice/radio_check/test/...    -> radio_check (test avvio)
        #   voice/acknowledge/radio_check/ -> MAIN (risposte "mi ricevi")
        #   tutto il resto                -> main
        #
        # La chiave: "acknowledge/radio_check" è un file principale,
        # ma "radio_check" e "radio_check_<Voice>" come figli diretti
        # di "voice/" sono file radio_check/spotter.

        # Secondo livello (primo sotto voice/)
        sub_dir = parts_lower[1] if len(parts_lower) >= 2 else ""

        if sub_dir.startswith("spotter"):
            spotter_files.append(wav)
        elif sub_dir.startswith("radio_check"):
            radio_check_files.append(wav)
        else:
            main_files.append(wav)

    return main_files, spotter_files, radio_check_files


def _copy_files(
    files: list[Path],
    source_dir: Path,
    dest_dir: Path,
    result: InstallResult,
    *,
    dry_run: bool = False,
    validate: bool = True,
) -> None:
    """Copia una lista di file nella cartella di destinazione, mantenendo
    la struttura relativa delle sotto-cartelle.

    Args:
        files: lista di file da copiare.
        source_dir: cartella radice sorgente (per calcolare i percorsi relativi).
        dest_dir: cartella di destinazione.
        result: oggetto InstallResult da aggiornare.
        dry_run: se True, non copia ma mostra cosa farebbe.
        validate: se True, verifica il formato WAV prima di copiare.
    """
    for src_file in files:
        rel_path = src_file.relative_to(source_dir)
        dest_file = dest_dir / rel_path

        # Validazione
        if validate:
            valid, msg = validate_wav_file(src_file)
            if not valid:
                result.files_invalid += 1
                result.errors.append(msg)
                logger.warning("File non valido: %s — %s", rel_path, msg)
                continue

        if dry_run:
            logger.debug("[DRY-RUN] Copierei: %s -> %s", rel_path, dest_file)
            result.files_copied += 1
            result.total_size_bytes += src_file.stat().st_size
            continue

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        result.files_copied += 1
        result.total_size_bytes += src_file.stat().st_size


def install_voicepack(
    voice_name: str,
    source_dir: Path,
    crewchief_dir: Path,
    *,
    backup: bool = True,
    dry_run: bool = False,
    validate: bool = True,
) -> InstallResult:
    """Installa un voice pack nella struttura di CrewChief V4.

    I file vengono distribuiti nelle cartelle corrette:
      - File principali → sounds/alt/<VoiceName>/
      - File spotter    → sounds/voice/spotter_<VoiceName>/
      - File radio check → sounds/voice/radio_check_<VoiceName>/

    Args:
        voice_name: nome della voce (es. "Marco").
        source_dir: cartella sorgente con i file generati.
        crewchief_dir: cartella radice dei dati utente di CrewChief.
        backup: se True, crea un backup prima dell'installazione.
        dry_run: se True, mostra cosa farebbe senza copiare.
        validate: se True, verifica il formato WAV prima di copiare.

    Returns:
        InstallResult con il riepilogo dell'installazione.
    """
    result = InstallResult()

    # Verifica sorgente
    if not source_dir.is_dir():
        result.errors.append(f"Cartella sorgente non trovata: {source_dir}")
        logger.error("Cartella sorgente non trovata: %s", source_dir)
        return result

    # Verifica destinazione
    sounds_dir = crewchief_dir / "sounds"
    if not sounds_dir.is_dir():
        result.errors.append(
            f"Cartella sounds di CrewChief non trovata: {sounds_dir}"
        )
        logger.error("Cartella sounds non trovata: %s", sounds_dir)
        return result

    # Conta file WAV nella sorgente
    wav_files = list(source_dir.rglob("*.wav"))
    if not wav_files:
        result.errors.append(f"Nessun file WAV trovato in: {source_dir}")
        logger.error("Nessun file WAV trovato in: %s", source_dir)
        return result

    logger.info(
        "Trovati %d file WAV nella sorgente: %s", len(wav_files), source_dir
    )

    # Backup
    if backup:
        create_backup(crewchief_dir, voice_name, dry_run=dry_run)

    # Classifica i file
    main_files, spotter_files, radio_check_files = _classify_source_files(
        source_dir, voice_name
    )

    logger.info(
        "Distribuzione file — principali: %d, spotter: %d, radio_check: %d",
        len(main_files),
        len(spotter_files),
        len(radio_check_files),
    )

    # Cartelle di destinazione
    alt_dest = sounds_dir / "alt" / voice_name
    spotter_dest = sounds_dir / "voice" / f"spotter_{voice_name}"
    radio_dest = sounds_dir / "voice" / f"radio_check_{voice_name}"

    prefix = "[DRY-RUN] " if dry_run else ""

    # Copia file principali
    if main_files:
        logger.info("%sInstallazione file principali in: %s", prefix, alt_dest)
        _copy_files(
            main_files, source_dir, alt_dest, result,
            dry_run=dry_run, validate=validate,
        )

    # Copia file spotter
    if spotter_files:
        logger.info("%sInstallazione file spotter in: %s", prefix, spotter_dest)
        # Per lo spotter, i percorsi relativi partono dalla sotto-cartella spotter
        # Troviamo la radice comune dei file spotter
        _copy_spotter_files(
            spotter_files, source_dir, spotter_dest, result,
            dry_run=dry_run, validate=validate,
        )

    # Copia file radio check
    if radio_check_files:
        logger.info("%sInstallazione file radio check in: %s", prefix, radio_dest)
        _copy_radio_check_files(
            radio_check_files, source_dir, radio_dest, result,
            dry_run=dry_run, validate=validate,
        )

    # Imposta sound_pack_language.txt a "it" per l'italiano
    lang_file = sounds_dir / "sound_pack_language.txt"
    if dry_run:
        logger.info("[DRY-RUN] Imposterei sound_pack_language.txt a 'it'")
    else:
        lang_file.write_text("it", encoding="utf-8")
        logger.info("sound_pack_language.txt impostato a 'it'")

    return result


def _copy_spotter_files(
    files: list[Path],
    source_dir: Path,
    dest_dir: Path,
    result: InstallResult,
    *,
    dry_run: bool = False,
    validate: bool = True,
) -> None:
    """Copia i file spotter mantenendo la struttura relativa sotto la
    sotto-cartella 'spotter' della sorgente."""
    for src_file in files:
        rel = src_file.relative_to(source_dir)
        # Rimuoviamo la parte 'spotter/' dal percorso relativo
        parts = list(rel.parts)
        spotter_idx = next(
            (i for i, p in enumerate(parts) if "spotter" in p.lower()), None
        )
        if spotter_idx is not None:
            sub_parts = parts[spotter_idx + 1:]
        else:
            sub_parts = parts

        dest_file = dest_dir / Path(*sub_parts) if sub_parts else dest_dir / rel.name

        if validate:
            valid, msg = validate_wav_file(src_file)
            if not valid:
                result.files_invalid += 1
                result.errors.append(msg)
                continue

        if dry_run:
            logger.debug("[DRY-RUN] Copierei spotter: %s -> %s", rel, dest_file)
            result.files_copied += 1
            result.total_size_bytes += src_file.stat().st_size
            continue

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        result.files_copied += 1
        result.total_size_bytes += src_file.stat().st_size


def _copy_radio_check_files(
    files: list[Path],
    source_dir: Path,
    dest_dir: Path,
    result: InstallResult,
    *,
    dry_run: bool = False,
    validate: bool = True,
) -> None:
    """Copia i file radio_check mantenendo la struttura relativa sotto la
    sotto-cartella 'radio_check' della sorgente."""
    for src_file in files:
        rel = src_file.relative_to(source_dir)
        parts = list(rel.parts)
        rc_idx = next(
            (i for i, p in enumerate(parts) if "radio_check" in p.lower()), None
        )
        if rc_idx is not None:
            sub_parts = parts[rc_idx + 1:]
        else:
            sub_parts = parts

        dest_file = dest_dir / Path(*sub_parts) if sub_parts else dest_dir / rel.name

        if validate:
            valid, msg = validate_wav_file(src_file)
            if not valid:
                result.files_invalid += 1
                result.errors.append(msg)
                continue

        if dry_run:
            logger.debug("[DRY-RUN] Copierei radio_check: %s -> %s", rel, dest_file)
            result.files_copied += 1
            result.total_size_bytes += src_file.stat().st_size
            continue

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        result.files_copied += 1
        result.total_size_bytes += src_file.stat().st_size


# ---------------------------------------------------------------------------
# Report finale
# ---------------------------------------------------------------------------


def print_summary(result: InstallResult, voice_name: str, *, dry_run: bool = False) -> None:
    """Stampa il riepilogo dell'installazione."""
    prefix = "[DRY-RUN] " if dry_run else ""
    size_mb = result.total_size_bytes / (1024 * 1024)

    print()
    print("=" * 60)
    print(f"  {prefix}RIEPILOGO INSTALLAZIONE — {voice_name}")
    print("=" * 60)
    print(f"  File copiati:    {result.files_copied}")
    print(f"  File non validi: {result.files_invalid}")
    print(f"  Dimensione:      {size_mb:.2f} MB")
    print()

    if result.warnings:
        print("  AVVISI:")
        for w in result.warnings:
            print(f"    ⚠ {w}")
        print()

    if result.errors:
        print("  ERRORI:")
        for e in result.errors:
            print(f"    ✗ {e}")
        print()

    if not result.errors and not result.files_invalid:
        print(f"  {prefix}Installazione completata con successo!")
    elif result.files_copied > 0:
        print(
            f"  {prefix}Installazione completata con {len(result.errors)} errori."
        )
    else:
        print(f"  {prefix}Installazione FALLITA.")

    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Analizza gli argomenti da riga di comando."""
    parser = argparse.ArgumentParser(
        description="Installa un voice pack italiano in CrewChief V4.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Esempi:\n"
            "  python install_voicepack.py --voice Marco\n"
            "  python install_voicepack.py --voice Marco --dry-run\n"
            "  python install_voicepack.py --voice Chiara --no-backup\n"
        ),
    )

    parser.add_argument(
        "--voice",
        required=True,
        help="Nome della voce da installare (es. Marco, Gianni, Chiara).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help=(
            "Cartella sorgente con i file audio generati. "
            "Default: ./output/<voice>"
        ),
    )
    parser.add_argument(
        "--crewchief-dir",
        type=Path,
        default=None,
        help=(
            "Cartella dati utente di CrewChief V4. "
            "Default: auto-rilevamento dal percorso standard."
        ),
    )
    parser.add_argument(
        "--backup",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Crea un backup del voice pack esistente prima di installare (default: si).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Mostra cosa verrebbe fatto senza copiare nessun file.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        default=False,
        help="Salta la validazione del formato WAV.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Output dettagliato (debug).",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Punto di ingresso principale dello script di installazione."""
    args = parse_args(argv)
    _setup_logging(args.verbose)

    voice_name: str = args.voice
    dry_run: bool = args.dry_run

    # Sorgente
    source_dir: Path = args.source or Path(f"./output/{voice_name}")
    source_dir = source_dir.resolve()

    # CrewChief dir
    crewchief_dir: Path | None = args.crewchief_dir
    if crewchief_dir is None:
        crewchief_dir = detect_crewchief_dir()
        if crewchief_dir is None:
            logger.error(
                "Impossibile trovare la cartella di CrewChief V4. "
                "Specifica il percorso con --crewchief-dir."
            )
            return 1
        logger.info("CrewChief trovato in: %s", crewchief_dir)
    else:
        crewchief_dir = crewchief_dir.resolve()

    if not crewchief_dir.is_dir():
        logger.error("La cartella di CrewChief non esiste: %s", crewchief_dir)
        return 1

    prefix = "[DRY-RUN] " if dry_run else ""
    logger.info("%sInstallazione voice pack '%s'", prefix, voice_name)
    logger.info("  Sorgente:    %s", source_dir)
    logger.info("  Destinazione: %s", crewchief_dir)

    # Installazione
    result = install_voicepack(
        voice_name=voice_name,
        source_dir=source_dir,
        crewchief_dir=crewchief_dir,
        backup=args.backup,
        dry_run=dry_run,
        validate=not args.no_validate,
    )

    print_summary(result, voice_name, dry_run=dry_run)

    if result.errors and result.files_copied == 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
