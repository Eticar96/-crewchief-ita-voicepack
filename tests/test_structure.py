"""Test per la validazione della struttura delle cartelle di output del voice pack."""

from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
VOICES_CONFIG = PROJECT_ROOT / "voice_generator" / "voices_config.yaml"

# Cartelle fondamentali che ogni voice pack deve avere
ESSENTIAL_VOICE_FOLDERS = [
    "acknowledge",
    "fuel",
    "lap_time",
    "penalties",
    "position",
    "session_start",
    "tyre_wear",
]

# Cartelle spotter obbligatorie
SPOTTER_FOLDERS = [
    "car_left",
    "car_right",
    "clear_all_round",
    "clear_left",
    "clear_right",
    "three_wide",
]

# File radio check attesi
RADIO_CHECK_FILES = [
    "1.wav",
]


def _skip_if_no_output() -> None:
    """Salta i test se la cartella output/ e' vuota o non esiste."""
    if not OUTPUT_DIR.exists() or not any(OUTPUT_DIR.iterdir()):
        pytest.skip(
            "Cartella output/ vuota o non esistente. "
            "Genera un voice pack prima di eseguire i test struttura."
        )


def _load_voices_config() -> dict:
    """Carica la configurazione delle voci da voices_config.yaml."""
    if not VOICES_CONFIG.exists():
        pytest.skip("voices_config.yaml non trovato")
    with open(VOICES_CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_voice_dirs() -> list[Path]:
    """Restituisce le cartelle voce presenti in output/."""
    if not OUTPUT_DIR.exists():
        return []
    return [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name != ".gitkeep"]


class TestOutputStructure:
    """Test per la struttura delle cartelle di output."""

    def test_output_structure(self) -> None:
        """Verifica che output/<VoiceName>/voice/ contenga le cartelle
        essenziali attese da CrewChief."""
        _skip_if_no_output()
        voice_dirs = _get_voice_dirs()

        assert len(voice_dirs) > 0, (
            "Nessuna cartella voce trovata in output/"
        )

        errors: list[str] = []
        for voice_dir in voice_dirs:
            voice_folder = voice_dir / "voice"
            if not voice_folder.exists():
                errors.append(
                    f"{voice_dir.name}: manca la cartella 'voice/'"
                )
                continue

            # Raccogliamo tutte le sottocartelle ricorsivamente
            existing_folders = {
                p.name for p in voice_folder.rglob("*") if p.is_dir()
            }

            for folder in ESSENTIAL_VOICE_FOLDERS:
                if folder not in existing_folders:
                    errors.append(
                        f"{voice_dir.name}: manca la cartella essenziale "
                        f"'voice/{folder}'"
                    )

        assert len(errors) == 0, (
            f"Problemi strutturali trovati (primi 10):\n"
            + "\n".join(errors[:10])
        )

    def test_spotter_files(self) -> None:
        """Verifica che le voci configurate come spotter abbiano i file
        nella struttura corretta."""
        _skip_if_no_output()
        config = _load_voices_config()
        voices = config.get("voices", {})

        spotter_voices = [
            name for name, cfg in voices.items()
            if cfg.get("use_as_spotter", False)
        ]

        if not spotter_voices:
            pytest.skip("Nessuna voce configurata come spotter")

        errors: list[str] = []
        for voice_name in spotter_voices:
            # Lo spotter puo' trovarsi in output/<voice>/voice/spotter/
            # oppure in output/<voice>/spotter/
            voice_dir = OUTPUT_DIR / voice_name
            if not voice_dir.exists():
                errors.append(f"{voice_name}: cartella voce non trovata")
                continue

            spotter_dir = voice_dir / "voice" / "spotter"
            if not spotter_dir.exists():
                spotter_dir = voice_dir / "spotter"

            if not spotter_dir.exists():
                errors.append(
                    f"{voice_name}: manca la cartella spotter"
                )
                continue

            existing_folders = {
                p.name for p in spotter_dir.iterdir() if p.is_dir()
            }
            for folder in SPOTTER_FOLDERS:
                if folder not in existing_folders:
                    errors.append(
                        f"{voice_name}: manca cartella spotter '{folder}'"
                    )

        assert len(errors) == 0, (
            f"Problemi spotter trovati:\n" + "\n".join(errors)
        )

    def test_radio_check_files(self) -> None:
        """Verifica che i file radio check esistano per ogni voce."""
        _skip_if_no_output()
        voice_dirs = _get_voice_dirs()

        if not voice_dirs:
            pytest.skip("Nessuna cartella voce in output/")

        errors: list[str] = []
        for voice_dir in voice_dirs:
            # Il radio check puo' essere in voice/radio_check/
            # o direttamente in radio_check/
            radio_dir = voice_dir / "voice" / "radio_check"
            if not radio_dir.exists():
                radio_dir = voice_dir / "radio_check"

            if not radio_dir.exists():
                errors.append(
                    f"{voice_dir.name}: manca la cartella radio_check"
                )
                continue

            wav_files = list(radio_dir.glob("*.wav"))
            if len(wav_files) == 0:
                errors.append(
                    f"{voice_dir.name}: cartella radio_check vuota"
                )

        assert len(errors) == 0, (
            f"Problemi radio check trovati:\n" + "\n".join(errors)
        )

    def test_alt_voice_structure(self) -> None:
        """Verifica che la struttura per voci alternative sia corretta.

        CrewChief si aspetta le voci alternative in:
        sounds/alt/<NomeVoce>/voice/
        Quindi output/<NomeVoce>/voice/ deve esistere e contenere file."""
        _skip_if_no_output()
        voice_dirs = _get_voice_dirs()

        if not voice_dirs:
            pytest.skip("Nessuna cartella voce in output/")

        errors: list[str] = []
        for voice_dir in voice_dirs:
            voice_subdir = voice_dir / "voice"
            if not voice_subdir.exists():
                errors.append(
                    f"{voice_dir.name}: manca 'voice/' sottocartella "
                    f"(richiesta da CrewChief per voci alternative)"
                )
                continue

            # Deve contenere almeno qualche sottocartella con file wav
            wav_count = len(list(voice_subdir.rglob("*.wav")))
            if wav_count == 0:
                errors.append(
                    f"{voice_dir.name}/voice/: nessun file .wav trovato"
                )

        assert len(errors) == 0, (
            f"Problemi struttura voce alternativa:\n" + "\n".join(errors)
        )
