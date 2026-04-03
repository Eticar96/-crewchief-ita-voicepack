"""Test per la validazione dei file audio generati dal progetto CrewChief ITA Voice Pack."""

import struct
import wave
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# Parametri audio attesi per CrewChief
EXPECTED_SAMPLE_RATE = 22050
EXPECTED_SAMPLE_WIDTH = 2  # 16-bit = 2 byte
EXPECTED_CHANNELS = 1  # mono

MIN_DURATION_SECONDS = 0.1
MAX_DURATION_SECONDS = 30.0
MAX_SILENCE_RATIO = 0.50  # massimo 50% di silenzio

# Soglia per considerare un campione come "silenzio" (valore assoluto 16-bit)
SILENCE_THRESHOLD = 500


def _collect_wav_files() -> list[Path]:
    """Raccoglie tutti i file .wav nella cartella output/."""
    if not OUTPUT_DIR.exists():
        return []
    return list(OUTPUT_DIR.rglob("*.wav"))


def _skip_if_no_output() -> None:
    """Salta i test se la cartella output/ e' vuota o non esiste."""
    wav_files = _collect_wav_files()
    if len(wav_files) == 0:
        pytest.skip(
            "Nessun file WAV trovato in output/. "
            "Genera un voice pack prima di eseguire i test audio."
        )


def _read_wav_info(filepath: Path) -> dict:
    """Legge le informazioni di base di un file WAV."""
    with wave.open(str(filepath), "rb") as wf:
        return {
            "channels": wf.getnchannels(),
            "sample_width": wf.getsampwidth(),
            "sample_rate": wf.getframerate(),
            "n_frames": wf.getnframes(),
            "duration": wf.getnframes() / wf.getframerate() if wf.getframerate() > 0 else 0,
        }


def _compute_silence_ratio(filepath: Path) -> float:
    """Calcola la percentuale di campioni sotto la soglia di silenzio."""
    with wave.open(str(filepath), "rb") as wf:
        n_frames = wf.getnframes()
        if n_frames == 0:
            return 1.0

        raw_data = wf.readframes(n_frames)
        # Interpretiamo come signed 16-bit little-endian
        n_samples = len(raw_data) // 2
        if n_samples == 0:
            return 1.0

        samples = struct.unpack(f"<{n_samples}h", raw_data)
        silent_count = sum(1 for s in samples if abs(s) < SILENCE_THRESHOLD)
        return silent_count / n_samples


class TestAudioFormat:
    """Test per il formato dei file audio generati."""

    def test_wav_format(self) -> None:
        """Verifica che tutti i file WAV siano 22050Hz, 16-bit, mono."""
        _skip_if_no_output()
        wav_files = _collect_wav_files()

        errors: list[str] = []
        for wav_path in wav_files:
            try:
                info = _read_wav_info(wav_path)
            except wave.Error as e:
                errors.append(f"{wav_path.name}: file WAV non valido ({e})")
                continue

            rel_path = wav_path.relative_to(OUTPUT_DIR)
            if info["sample_rate"] != EXPECTED_SAMPLE_RATE:
                errors.append(
                    f"{rel_path}: sample rate {info['sample_rate']} "
                    f"(atteso {EXPECTED_SAMPLE_RATE})"
                )
            if info["sample_width"] != EXPECTED_SAMPLE_WIDTH:
                errors.append(
                    f"{rel_path}: bit depth {info['sample_width'] * 8}-bit "
                    f"(atteso {EXPECTED_SAMPLE_WIDTH * 8}-bit)"
                )
            if info["channels"] != EXPECTED_CHANNELS:
                errors.append(
                    f"{rel_path}: {info['channels']} canali "
                    f"(atteso {EXPECTED_CHANNELS} - mono)"
                )

        assert len(errors) == 0, (
            f"Trovati {len(errors)} file con formato errato "
            f"(primi 10):\n" + "\n".join(errors[:10])
        )

    def test_no_empty_files(self) -> None:
        """Verifica che nessun file WAV abbia dimensione 0 byte."""
        _skip_if_no_output()
        wav_files = _collect_wav_files()

        empty_files = [f for f in wav_files if f.stat().st_size == 0]

        assert len(empty_files) == 0, (
            f"Trovati {len(empty_files)} file WAV vuoti (0 byte) "
            f"(primi 10): {[str(f.relative_to(OUTPUT_DIR)) for f in empty_files[:10]]}"
        )

    def test_duration_range(self) -> None:
        """Verifica che la durata dei file sia tra 0.1s e 30s."""
        _skip_if_no_output()
        wav_files = _collect_wav_files()

        out_of_range: list[str] = []
        for wav_path in wav_files:
            try:
                info = _read_wav_info(wav_path)
            except wave.Error:
                continue  # gestito da test_wav_format

            duration = info["duration"]
            rel_path = wav_path.relative_to(OUTPUT_DIR)
            if duration < MIN_DURATION_SECONDS:
                out_of_range.append(f"{rel_path}: {duration:.3f}s (troppo corto)")
            elif duration > MAX_DURATION_SECONDS:
                out_of_range.append(f"{rel_path}: {duration:.1f}s (troppo lungo)")

        assert len(out_of_range) == 0, (
            f"Trovati {len(out_of_range)} file con durata fuori range "
            f"[{MIN_DURATION_SECONDS}s - {MAX_DURATION_SECONDS}s] "
            f"(primi 10):\n" + "\n".join(out_of_range[:10])
        )

    def test_no_excessive_silence(self) -> None:
        """Verifica che i file non contengano piu' del 50% di silenzio."""
        _skip_if_no_output()
        wav_files = _collect_wav_files()

        # Testa un campione (max 200 file) per non rallentare troppo
        sample_size = min(200, len(wav_files))
        sample = wav_files[:sample_size]

        too_silent: list[str] = []
        for wav_path in sample:
            try:
                ratio = _compute_silence_ratio(wav_path)
            except (wave.Error, struct.error):
                continue

            if ratio > MAX_SILENCE_RATIO:
                rel_path = wav_path.relative_to(OUTPUT_DIR)
                too_silent.append(f"{rel_path}: {ratio:.0%} silenzio")

        assert len(too_silent) == 0, (
            f"Trovati {len(too_silent)} file con silenzio eccessivo "
            f"(>{MAX_SILENCE_RATIO:.0%}) "
            f"(primi 10):\n" + "\n".join(too_silent[:10])
        )
