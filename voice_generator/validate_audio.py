#!/usr/bin/env python3
"""
validate_audio.py — Validazione dei file audio generati per CrewChief ITA Voice Pack.

Controlla formato, durata, silenzio e clipping di tutti i file WAV generati.
Opzionalmente tenta di correggere i problemi risolvibili automaticamente.

Uso:
    python validate_audio.py --input-dir ./output
    python validate_audio.py --voice Marco --fix
    python validate_audio.py --input-dir ./output --report report.txt
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import wave
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import numpy as np

try:
    import soundfile as sf
except ImportError:
    sf = None  # type: ignore[assignment]

try:
    import librosa
except ImportError:
    librosa = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------

REQUIRED_SAMPLE_RATE = 22050
REQUIRED_CHANNELS = 1
REQUIRED_BIT_DEPTH = 16
REQUIRED_SUBTYPE = "PCM_16"

MIN_DURATION_SEC = 0.1        # sotto questa soglia = sospetto
MAX_DURATION_SEC = 30.0       # sopra questa soglia = sospetto
SILENCE_THRESHOLD_DB = -40.0  # soglia per considerare un campione silenzio
SILENCE_RATIO_WARN = 0.50     # avviso se > 50% silenzio
CLIPPING_THRESHOLD = 0.99     # campioni normalizzati oltre questa soglia = clipping
CLIPPING_RATIO_WARN = 0.001   # avviso se > 0.1% dei campioni è clipping

logger = logging.getLogger("validate_audio")


# ---------------------------------------------------------------------------
# Tipi
# ---------------------------------------------------------------------------


class Severity(Enum):
    """Livello di gravità di un problema riscontrato."""
    OK = "OK"
    WARNING = "AVVISO"
    ERROR = "ERRORE"


@dataclass
class FileIssue:
    """Singolo problema riscontrato in un file audio."""
    severity: Severity
    code: str
    message: str
    fixable: bool = False


@dataclass
class FileReport:
    """Report di validazione di un singolo file."""
    path: Path
    issues: list[FileIssue] = field(default_factory=list)

    @property
    def worst_severity(self) -> Severity:
        """Restituisce la gravità peggiore tra tutti i problemi."""
        if not self.issues:
            return Severity.OK
        if any(i.severity == Severity.ERROR for i in self.issues):
            return Severity.ERROR
        if any(i.severity == Severity.WARNING for i in self.issues):
            return Severity.WARNING
        return Severity.OK

    @property
    def has_fixable_issues(self) -> bool:
        """Indica se ci sono problemi correggibili automaticamente."""
        return any(i.fixable for i in self.issues)


@dataclass
class ValidationSummary:
    """Riepilogo della validazione di tutti i file."""
    total_files: int = 0
    ok_files: int = 0
    warning_files: int = 0
    error_files: int = 0
    fixed_files: int = 0
    file_reports: list[FileReport] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _setup_logging(verbose: bool = False) -> None:
    """Configura il logging con output strutturato."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s | %(levelname)-7s | %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S")


# ---------------------------------------------------------------------------
# Validazione
# ---------------------------------------------------------------------------


def _check_format(filepath: Path, report: FileReport) -> bool:
    """Verifica formato WAV: sample rate, bit depth, canali.

    Returns:
        True se il file e' leggibile, False se non e' stato possibile aprirlo.
    """
    try:
        with wave.open(str(filepath), "rb") as wf:
            sr = wf.getframerate()
            ch = wf.getnchannels()
            sw = wf.getsampwidth()
            bit_depth = sw * 8

            if sr != REQUIRED_SAMPLE_RATE:
                report.issues.append(FileIssue(
                    severity=Severity.ERROR,
                    code="WRONG_SAMPLE_RATE",
                    message=f"Sample rate {sr} Hz (richiesto {REQUIRED_SAMPLE_RATE} Hz)",
                    fixable=True,
                ))

            if bit_depth != REQUIRED_BIT_DEPTH:
                report.issues.append(FileIssue(
                    severity=Severity.ERROR,
                    code="WRONG_BIT_DEPTH",
                    message=f"Bit depth {bit_depth}-bit (richiesto {REQUIRED_BIT_DEPTH}-bit)",
                    fixable=True,
                ))

            if ch != REQUIRED_CHANNELS:
                report.issues.append(FileIssue(
                    severity=Severity.ERROR,
                    code="WRONG_CHANNELS",
                    message=f"{ch} canali (richiesto mono)",
                    fixable=True,
                ))

            return True

    except wave.Error as exc:
        report.issues.append(FileIssue(
            severity=Severity.ERROR,
            code="INVALID_WAV",
            message=f"File WAV non valido: {exc}",
            fixable=False,
        ))
        return False
    except Exception as exc:  # noqa: BLE001
        report.issues.append(FileIssue(
            severity=Severity.ERROR,
            code="READ_ERROR",
            message=f"Errore nella lettura: {exc}",
            fixable=False,
        ))
        return False


def _check_empty(filepath: Path, report: FileReport) -> None:
    """Verifica che il file non sia vuoto (0 byte)."""
    if filepath.stat().st_size == 0:
        report.issues.append(FileIssue(
            severity=Severity.ERROR,
            code="EMPTY_FILE",
            message="File vuoto (0 byte)",
            fixable=False,
        ))


def _check_duration_and_content(filepath: Path, report: FileReport) -> None:
    """Verifica durata, silenzio eccessivo e clipping usando librosa/soundfile.

    Richiede librosa e soundfile installati. Se non disponibili, salta i
    controlli avanzati con un avviso.
    """
    if sf is None or librosa is None:
        logger.debug(
            "librosa/soundfile non disponibili, salto controlli avanzati per %s",
            filepath.name,
        )
        return

    try:
        audio, sr = sf.read(str(filepath), dtype="float32")
    except Exception as exc:  # noqa: BLE001
        report.issues.append(FileIssue(
            severity=Severity.ERROR,
            code="SF_READ_ERROR",
            message=f"Impossibile leggere con soundfile: {exc}",
            fixable=False,
        ))
        return

    # Se stereo, prendi solo il primo canale per l'analisi
    if audio.ndim > 1:
        audio = audio[:, 0]

    n_samples = len(audio)
    if n_samples == 0:
        report.issues.append(FileIssue(
            severity=Severity.ERROR,
            code="NO_SAMPLES",
            message="File senza campioni audio",
            fixable=False,
        ))
        return

    duration = n_samples / sr

    # Durata troppo corta
    if duration < MIN_DURATION_SEC:
        report.issues.append(FileIssue(
            severity=Severity.WARNING,
            code="TOO_SHORT",
            message=f"Durata sospettamente breve: {duration:.3f}s (soglia {MIN_DURATION_SEC}s)",
            fixable=False,
        ))

    # Durata troppo lunga
    if duration > MAX_DURATION_SEC:
        report.issues.append(FileIssue(
            severity=Severity.WARNING,
            code="TOO_LONG",
            message=f"Durata sospettamente lunga: {duration:.1f}s (soglia {MAX_DURATION_SEC}s)",
            fixable=False,
        ))

    # Silenzio eccessivo
    amplitude_db = librosa.amplitude_to_db(np.abs(audio), ref=1.0)
    silent_samples = np.sum(amplitude_db < SILENCE_THRESHOLD_DB)
    silence_ratio = silent_samples / n_samples

    if silence_ratio > SILENCE_RATIO_WARN:
        report.issues.append(FileIssue(
            severity=Severity.WARNING,
            code="EXCESSIVE_SILENCE",
            message=f"Silenzio eccessivo: {silence_ratio:.0%} del file (soglia {SILENCE_RATIO_WARN:.0%})",
            fixable=True,
        ))

    # Clipping
    clipping_samples = np.sum(np.abs(audio) >= CLIPPING_THRESHOLD)
    clipping_ratio = clipping_samples / n_samples

    if clipping_ratio > CLIPPING_RATIO_WARN:
        report.issues.append(FileIssue(
            severity=Severity.WARNING,
            code="CLIPPING",
            message=f"Clipping rilevato: {clipping_samples} campioni ({clipping_ratio:.2%})",
            fixable=True,
        ))


def validate_file(filepath: Path) -> FileReport:
    """Esegue tutte le verifiche su un singolo file WAV.

    Args:
        filepath: percorso del file WAV.

    Returns:
        FileReport con tutti i problemi riscontrati.
    """
    report = FileReport(path=filepath)

    # File vuoto
    _check_empty(filepath, report)
    if any(i.code == "EMPTY_FILE" for i in report.issues):
        return report

    # Formato
    readable = _check_format(filepath, report)

    # Durata e contenuto (richiede librosa/soundfile)
    if readable:
        _check_duration_and_content(filepath, report)

    return report


# ---------------------------------------------------------------------------
# Correzione automatica
# ---------------------------------------------------------------------------


def fix_file(filepath: Path, report: FileReport) -> bool:
    """Tenta di correggere i problemi risolvibili di un file WAV.

    Operazioni possibili:
      - Conversione sample rate a 22050 Hz
      - Conversione a mono
      - Conversione a 16-bit PCM
      - Trim del silenzio iniziale/finale
      - Ri-normalizzazione per evitare clipping

    Args:
        filepath: percorso del file WAV.
        report: report di validazione del file.

    Returns:
        True se il file e' stato corretto con successo.
    """
    if sf is None or librosa is None:
        logger.error(
            "librosa e soundfile sono necessari per la correzione automatica."
        )
        return False

    fixable_codes = {i.code for i in report.issues if i.fixable}
    if not fixable_codes:
        return False

    try:
        audio, sr = sf.read(str(filepath), dtype="float32")
    except Exception as exc:  # noqa: BLE001
        logger.error("Impossibile leggere %s per la correzione: %s", filepath.name, exc)
        return False

    modified = False

    # Conversione a mono
    if "WRONG_CHANNELS" in fixable_codes and audio.ndim > 1:
        logger.debug("  Conversione a mono: %s", filepath.name)
        audio = np.mean(audio, axis=1)
        modified = True

    # Conversione sample rate
    if "WRONG_SAMPLE_RATE" in fixable_codes and sr != REQUIRED_SAMPLE_RATE:
        logger.debug(
            "  Resampling %d -> %d Hz: %s", sr, REQUIRED_SAMPLE_RATE, filepath.name
        )
        audio = librosa.resample(audio, orig_sr=sr, target_sr=REQUIRED_SAMPLE_RATE)
        sr = REQUIRED_SAMPLE_RATE
        modified = True

    # Trim silenzio
    if "EXCESSIVE_SILENCE" in fixable_codes:
        logger.debug("  Trim silenzio: %s", filepath.name)
        trimmed, _ = librosa.effects.trim(audio, top_db=abs(SILENCE_THRESHOLD_DB))
        if len(trimmed) > 0:
            audio = trimmed
            modified = True

    # Normalizzazione (anti-clipping)
    if "CLIPPING" in fixable_codes:
        logger.debug("  Normalizzazione: %s", filepath.name)
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio * (0.95 / peak)
            modified = True

    if modified:
        try:
            sf.write(str(filepath), audio, sr, subtype=REQUIRED_SUBTYPE)
            logger.info("  Corretto: %s", filepath.name)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Errore nella scrittura di %s: %s", filepath.name, exc)
            return False

    return False


# ---------------------------------------------------------------------------
# Scansione e report
# ---------------------------------------------------------------------------


def validate_directory(
    input_dir: Path,
    *,
    fix: bool = False,
) -> ValidationSummary:
    """Valida tutti i file WAV in una cartella (ricorsivamente).

    Args:
        input_dir: cartella da scansionare.
        fix: se True, tenta di correggere i problemi risolvibili.

    Returns:
        ValidationSummary con il riepilogo completo.
    """
    summary = ValidationSummary()

    wav_files = sorted(input_dir.rglob("*.wav"))
    summary.total_files = len(wav_files)

    if not wav_files:
        logger.warning("Nessun file WAV trovato in: %s", input_dir)
        return summary

    logger.info("Scansione di %d file WAV in: %s", len(wav_files), input_dir)

    for i, wav_path in enumerate(wav_files, 1):
        if i % 500 == 0 or i == len(wav_files):
            logger.info("  Progresso: %d/%d file analizzati...", i, len(wav_files))

        report = validate_file(wav_path)

        severity = report.worst_severity
        if severity == Severity.OK:
            summary.ok_files += 1
        elif severity == Severity.WARNING:
            summary.warning_files += 1
        elif severity == Severity.ERROR:
            summary.error_files += 1

        # Correzione automatica
        if fix and report.has_fixable_issues:
            fixed = fix_file(wav_path, report)
            if fixed:
                summary.fixed_files += 1

        summary.file_reports.append(report)

    return summary


def print_summary(summary: ValidationSummary) -> None:
    """Stampa il riepilogo della validazione a console."""
    print()
    print("=" * 60)
    print("  RIEPILOGO VALIDAZIONE AUDIO")
    print("=" * 60)
    print(f"  File analizzati: {summary.total_files}")
    print(f"  OK:              {summary.ok_files}")
    print(f"  Avvisi:          {summary.warning_files}")
    print(f"  Errori:          {summary.error_files}")
    if summary.fixed_files > 0:
        print(f"  Corretti:        {summary.fixed_files}")
    print()

    # Dettagli errori
    error_reports = [r for r in summary.file_reports if r.worst_severity == Severity.ERROR]
    if error_reports:
        print("  FILE CON ERRORI:")
        for report in error_reports[:50]:  # limita l'output
            rel = report.path.name
            for issue in report.issues:
                if issue.severity == Severity.ERROR:
                    print(f"    [ERRORE] {rel}: {issue.message}")
        if len(error_reports) > 50:
            print(f"    ... e altri {len(error_reports) - 50} file con errori.")
        print()

    # Dettagli avvisi
    warning_reports = [r for r in summary.file_reports if r.worst_severity == Severity.WARNING]
    if warning_reports:
        print("  FILE CON AVVISI:")
        for report in warning_reports[:30]:
            rel = report.path.name
            for issue in report.issues:
                if issue.severity == Severity.WARNING:
                    print(f"    [AVVISO] {rel}: {issue.message}")
        if len(warning_reports) > 30:
            print(f"    ... e altri {len(warning_reports) - 30} file con avvisi.")
        print()

    # Risultato finale
    if summary.error_files == 0 and summary.warning_files == 0:
        print("  Tutti i file sono validi!")
    elif summary.error_files == 0:
        print(f"  Nessun errore critico, {summary.warning_files} avvisi da verificare.")
    else:
        print(f"  {summary.error_files} file con errori richiedono attenzione.")
    print("=" * 60)
    print()


def save_report(summary: ValidationSummary, report_path: Path) -> None:
    """Salva il report di validazione su file in formato JSON.

    Args:
        summary: riepilogo della validazione.
        report_path: percorso del file di output.
    """
    data: dict = {
        "totale_file": summary.total_files,
        "ok": summary.ok_files,
        "avvisi": summary.warning_files,
        "errori": summary.error_files,
        "corretti": summary.fixed_files,
        "dettagli": [],
    }

    for report in summary.file_reports:
        if report.worst_severity == Severity.OK:
            continue
        file_data: dict = {
            "file": str(report.path),
            "gravita": report.worst_severity.value,
            "problemi": [
                {
                    "gravita": issue.severity.value,
                    "codice": issue.code,
                    "messaggio": issue.message,
                    "correggibile": issue.fixable,
                }
                for issue in report.issues
            ],
        }
        data["dettagli"].append(file_data)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("Report salvato in: %s", report_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Analizza gli argomenti da riga di comando."""
    parser = argparse.ArgumentParser(
        description="Validazione dei file audio generati per CrewChief ITA Voice Pack.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Esempi:\n"
            "  python validate_audio.py --input-dir ./output\n"
            "  python validate_audio.py --voice Marco --fix\n"
            "  python validate_audio.py --input-dir ./output --report report.json\n"
        ),
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("./output"),
        help="Cartella con i file audio da validare (default: ./output).",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default=None,
        help="Valida solo i file di una voce specifica (sotto-cartella di input-dir).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="Tenta di correggere automaticamente i problemi risolvibili.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Salva il report di validazione in un file JSON.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Output dettagliato (debug).",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Punto di ingresso principale dello script di validazione."""
    args = parse_args(argv)
    _setup_logging(args.verbose)

    # Determina la cartella di input
    input_dir: Path = args.input_dir.resolve()
    if args.voice:
        input_dir = input_dir / args.voice

    if not input_dir.is_dir():
        logger.error("Cartella non trovata: %s", input_dir)
        return 1

    # Verifica dipendenze
    if sf is None:
        logger.warning(
            "soundfile non installato: i controlli avanzati saranno limitati. "
            "Installa con: pip install soundfile"
        )
    if librosa is None:
        logger.warning(
            "librosa non installato: i controlli avanzati saranno limitati. "
            "Installa con: pip install librosa"
        )

    if args.fix and (sf is None or librosa is None):
        logger.error(
            "La modalita' --fix richiede soundfile e librosa installati."
        )
        return 1

    # Validazione
    summary = validate_directory(input_dir, fix=args.fix)

    # Output
    print_summary(summary)

    if args.report:
        save_report(summary, args.report.resolve())

    # Exit code
    if summary.error_files > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
