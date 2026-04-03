"""Test per la validazione dei file lessico CSV del progetto CrewChief ITA Voice Pack."""

import csv
import os
from pathlib import Path

import pytest

# Percorsi base
PROJECT_ROOT = Path(__file__).parent.parent
LEXICON_DIR = PROJECT_ROOT / "lexicon"
PHRASE_INVENTORY_ITA = LEXICON_DIR / "phrase_inventory_ita.csv"
PHRASE_INVENTORY_ORIGINAL = LEXICON_DIR / "phrase_inventory_original.csv"
CUSTOM_PHRASES = LEXICON_DIR / "custom_phrases.csv"
SWEAR_PHRASES = LEXICON_DIR / "swear_phrases.csv"
LMU_PHRASES = LEXICON_DIR / "lmu_specific_phrases.csv"

EXPECTED_COLUMNS = ["audio_path", "audio_filename", "subtitle", "text_for_tts"]

# Prefissi cartelle conosciuti nella struttura CrewChief
KNOWN_TOPLEVEL_FOLDERS = [
    r"\voice",
    r"\spotter",
]


def _read_csv(filepath: Path) -> list[dict[str, str]]:
    """Legge un file CSV e restituisce una lista di dizionari."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _read_csv_header(filepath: Path) -> list[str]:
    """Legge solo l'header di un file CSV."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return next(reader)


# ---------------------------------------------------------------------------
# Test principali per phrase_inventory_ita.csv
# ---------------------------------------------------------------------------


class TestPhraseInventoryIta:
    """Test per il file phrase_inventory_ita.csv."""

    def test_phrase_inventory_ita_exists(self) -> None:
        """Verifica che il file phrase_inventory_ita.csv esista."""
        assert PHRASE_INVENTORY_ITA.exists(), (
            f"File non trovato: {PHRASE_INVENTORY_ITA}. "
            "Esegui lo script di arricchimento lessico per generarlo."
        )

    @pytest.mark.skipif(
        not PHRASE_INVENTORY_ITA.exists(),
        reason="phrase_inventory_ita.csv non ancora generato",
    )
    def test_csv_format(self) -> None:
        """Verifica che il CSV abbia le colonne corrette."""
        header = _read_csv_header(PHRASE_INVENTORY_ITA)
        assert header == EXPECTED_COLUMNS, (
            f"Colonne attese: {EXPECTED_COLUMNS}, trovate: {header}"
        )

    @pytest.mark.skipif(
        not PHRASE_INVENTORY_ITA.exists(),
        reason="phrase_inventory_ita.csv non ancora generato",
    )
    def test_no_empty_fields(self) -> None:
        """Verifica che nessun campo subtitle o text_for_tts sia vuoto."""
        rows = _read_csv(PHRASE_INVENTORY_ITA)
        assert len(rows) > 0, "Il CSV e' vuoto"

        empty_rows: list[int] = []
        for i, row in enumerate(rows, start=2):  # riga 1 e' l'header
            subtitle = row.get("subtitle", "").strip()
            text_for_tts = row.get("text_for_tts", "").strip()
            if not subtitle or not text_for_tts:
                empty_rows.append(i)

        assert len(empty_rows) == 0, (
            f"Trovate {len(empty_rows)} righe con campi vuoti "
            f"(prime 10): {empty_rows[:10]}"
        )

    @pytest.mark.skipif(
        not PHRASE_INVENTORY_ITA.exists(),
        reason="phrase_inventory_ita.csv non ancora generato",
    )
    def test_folder_paths_valid(self) -> None:
        """Verifica che tutti i valori audio_path inizino con backslash
        e corrispondano alla struttura nota di CrewChief."""
        rows = _read_csv(PHRASE_INVENTORY_ITA)
        invalid_paths: list[tuple[int, str]] = []

        for i, row in enumerate(rows, start=2):
            audio_path = row.get("audio_path", "")
            if not audio_path.startswith("\\"):
                invalid_paths.append((i, audio_path))
                continue
            # Verifica che il percorso inizi con uno dei prefissi noti
            if not any(audio_path.startswith(prefix) for prefix in KNOWN_TOPLEVEL_FOLDERS):
                invalid_paths.append((i, audio_path))

        assert len(invalid_paths) == 0, (
            f"Trovati {len(invalid_paths)} percorsi non validi "
            f"(primi 10): {invalid_paths[:10]}"
        )

    @pytest.mark.skipif(
        not PHRASE_INVENTORY_ITA.exists() or not PHRASE_INVENTORY_ORIGINAL.exists(),
        reason="Uno dei file CSV non disponibile",
    )
    def test_original_coverage(self) -> None:
        """Verifica che il CSV italiano copra almeno il 90% delle cartelle
        presenti nel file originale inglese."""
        original_rows = _read_csv(PHRASE_INVENTORY_ORIGINAL)
        ita_rows = _read_csv(PHRASE_INVENTORY_ITA)

        original_folders = {row["audio_path"] for row in original_rows}
        ita_folders = {row["audio_path"] for row in ita_rows}

        if len(original_folders) == 0:
            pytest.skip("File originale vuoto")

        coverage = len(ita_folders & original_folders) / len(original_folders)
        assert coverage >= 0.90, (
            f"Copertura cartelle insufficiente: {coverage:.1%} "
            f"(minimo richiesto: 90%). "
            f"Cartelle mancanti: {len(original_folders - ita_folders)}"
        )

    @pytest.mark.skipif(
        not PHRASE_INVENTORY_ITA.exists(),
        reason="phrase_inventory_ita.csv non ancora generato",
    )
    def test_no_duplicate_entries(self) -> None:
        """Verifica che non ci siano righe duplicate esatte."""
        rows = _read_csv(PHRASE_INVENTORY_ITA)
        seen: set[tuple[str, ...]] = set()
        duplicates: list[int] = []

        for i, row in enumerate(rows, start=2):
            key = tuple(row.values())
            if key in seen:
                duplicates.append(i)
            seen.add(key)

        assert len(duplicates) == 0, (
            f"Trovate {len(duplicates)} righe duplicate "
            f"(prime 10): {duplicates[:10]}"
        )


# ---------------------------------------------------------------------------
# Test per i file CSV supplementari
# ---------------------------------------------------------------------------


def _validate_supplementary_csv(filepath: Path) -> None:
    """Validazione comune per i CSV supplementari."""
    assert filepath.exists(), f"File non trovato: {filepath}"

    header = _read_csv_header(filepath)
    assert header == EXPECTED_COLUMNS, (
        f"Colonne attese in {filepath.name}: {EXPECTED_COLUMNS}, "
        f"trovate: {header}"
    )

    rows = _read_csv(filepath)
    assert len(rows) > 0, f"Il file {filepath.name} e' vuoto"

    empty_rows: list[int] = []
    for i, row in enumerate(rows, start=2):
        subtitle = row.get("subtitle", "").strip()
        text_for_tts = row.get("text_for_tts", "").strip()
        if not subtitle or not text_for_tts:
            empty_rows.append(i)

    assert len(empty_rows) == 0, (
        f"Trovate {len(empty_rows)} righe con campi vuoti in {filepath.name} "
        f"(prime 10): {empty_rows[:10]}"
    )


def test_custom_phrases_format() -> None:
    """Verifica formato e contenuto di custom_phrases.csv."""
    _validate_supplementary_csv(CUSTOM_PHRASES)


def test_swear_phrases_format() -> None:
    """Verifica formato e contenuto di swear_phrases.csv."""
    _validate_supplementary_csv(SWEAR_PHRASES)


def test_lmu_phrases_format() -> None:
    """Verifica formato e contenuto di lmu_specific_phrases.csv."""
    _validate_supplementary_csv(LMU_PHRASES)
