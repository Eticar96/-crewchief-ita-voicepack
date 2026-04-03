#!/usr/bin/env python3
"""Generatore principale di voice pack italiani per CrewChief V4.

Legge la configurazione voci da voices_config.yaml e genera file audio WAV
utilizzando Coqui XTTS v2 per la sintesi vocale in italiano.
"""

import argparse
import csv
import logging
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from tqdm import tqdm

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class PhraseEntry:
    """Voce del phrase inventory."""

    audio_path: str
    audio_filename: str
    subtitle: str
    text_for_tts: str


def load_config(config_path: str) -> dict:
    """Carica la configurazione voci da file YAML."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def load_phrase_inventory(csv_path: str) -> list[PhraseEntry]:
    """Carica il phrase inventory dal file CSV."""
    entries: list[PhraseEntry] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if len(row) < 4:
                continue
            entries.append(PhraseEntry(
                audio_path=row[0],
                audio_filename=row[1],
                subtitle=row[2],
                text_for_tts=row[3],
            ))
    return entries


def init_tts_model(
    reference_audio_dir: str,
    language: str = "it",
    device: str = "cuda",
) -> object:
    """Inizializza il modello XTTS v2 con gli audio di riferimento.

    Restituisce il modello TTS pronto per la generazione.
    Richiede coqui-tts installato (disponibile nel container Docker).
    """
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
    except ImportError:
        logger.error(
            "coqui-tts non installato. Usa il container Docker per la generazione:\n"
            "  docker compose up\n"
            "Oppure installa manualmente:\n"
            "  pip install coqui-tts"
        )
        sys.exit(1)

    import torch

    # Percorso modello XTTS v2
    model_path = os.path.expanduser(
        "~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
    )
    if not os.path.exists(model_path):
        # Prova percorso alternativo Windows
        model_path = os.path.join(
            os.environ.get("APPDATA", ""), "tts",
            "tts_models--multilingual--multi-dataset--xtts_v2"
        )

    if not os.path.exists(model_path):
        logger.error(
            f"Modello XTTS v2 non trovato. Scaricalo con:\n"
            f"  git clone --branch v2.0.3 https://huggingface.co/coqui/XTTS-v2 {model_path}"
        )
        sys.exit(1)

    logger.info("Caricamento modello XTTS v2...")
    config = XttsConfig()
    config.load_json(os.path.join(model_path, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=model_path)

    if device == "cuda" and torch.cuda.is_available():
        model.cuda()
        logger.info("Modello caricato su GPU")
    else:
        logger.info("Modello caricato su CPU (generazione piu lenta)")

    # Carica audio di riferimento
    ref_files = []
    ref_dir = Path(reference_audio_dir)
    if ref_dir.exists():
        for ext in ("*.wav", "*.mp3", "*.flac"):
            ref_files.extend(ref_dir.glob(ext))

    if not ref_files:
        logger.error(f"Nessun file audio di riferimento trovato in {reference_audio_dir}")
        sys.exit(1)

    logger.info(f"Audio di riferimento: {len(ref_files)} file da {reference_audio_dir}")

    # Calcola latent per la voce di riferimento
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=[str(f) for f in ref_files],
    )
    model._ref_latents = (gpt_cond_latent, speaker_embedding)
    model._language = language

    return model


def generate_audio(
    model: object,
    text: str,
    output_path: str,
    speed: float = 1.4,
) -> bool:
    """Genera un file audio WAV dal testo usando XTTS v2.

    Restituisce True se il file e stato generato con successo.
    """
    import torch
    import torchaudio

    try:
        gpt_cond_latent, speaker_embedding = model._ref_latents
        language = model._language

        out = model.inference(
            text,
            language,
            gpt_cond_latent,
            speaker_embedding,
            speed=speed,
        )

        wav = torch.tensor(out["wav"]).unsqueeze(0)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        torchaudio.save(output_path, wav, 24000)  # XTTS genera a 24kHz

        return True

    except Exception as e:
        logger.warning(f"Errore generazione audio per '{text[:50]}...': {e}")
        return False


def apply_audio_effects(input_path: str, output_path: str) -> bool:
    """Applica effetti audio per simulare radio motorsport.

    Effetti: EQ radio, leggero overdrive, trim silenzio,
    normalizzazione, downsample a 22050Hz mono 16-bit.
    """
    sox_command = [
        "sox", "-V1", "-q",
        input_path, "-b", "16", output_path,
        # EQ: taglia bassi, enfatizza medi/alti (effetto radio)
        "equalizer", "100", "0.5q", "-12",
        "equalizer", "200", "0.5q", "-6",
        "equalizer", "300", "0.5q", "-3",
        "equalizer", "3000", "0.5q", "6",
        "equalizer", "6000", "0.5q", "4",
        "equalizer", "10000", "0.5q", "3",
        # Leggero overdrive
        "overdrive", "7", "12",
        # Trim silenzio iniziale e finale
        "silence", "1", "0.1", "0.1%",
        "reverse",
        "silence", "1", "0.1", "0.3%",
        "reverse",
        # Normalizza
        "norm", "-1",
        # Mono, 22050Hz
        "channels", "1",
        "rate", "22050",
    ]

    try:
        subprocess.run(sox_command, check=True, capture_output=True)
        return True
    except FileNotFoundError:
        logger.warning("sox non trovato. Installa SoX per applicare effetti audio.")
        # Fallback: copia semplice senza effetti
        import shutil
        shutil.copy2(input_path, output_path)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Errore SoX: {e}")
        return False


def validate_wav(file_path: str, text: str) -> bool:
    """Validazione base di un file WAV generato.

    Controlla che il file esista, non sia vuoto e abbia durata ragionevole.
    """
    if not os.path.exists(file_path):
        return False

    file_size = os.path.getsize(file_path)
    if file_size < 1000:  # < 1KB probabilmente corrotto
        return False

    try:
        import soundfile as sf
        info = sf.info(file_path)
        duration = info.duration

        # Troppo corto o troppo lungo
        if duration < 0.1 or duration > 30.0:
            return False

        # Durata proporzionale al testo
        words = len(text.split())
        if words > 3 and duration < 0.3:
            return False

    except Exception:
        return False

    return True


def generate_radio_check(
    model: object,
    voice_name: str,
    voice_name_tts: str,
    output_dir: str,
    speed: float = 1.4,
) -> None:
    """Genera i file audio di radio check per una voce."""
    radio_phrases = [
        f"Ciao, sono {voice_name_tts}, il tuo ingegnere di pista. Mi ricevi?",
        f"Radio check, qui {voice_name_tts}. Tutto funziona correttamente.",
        f"Prova radio, {voice_name_tts} in linea. Siamo pronti.",
        f"Eccomi, sono {voice_name_tts}. Comunicazione attiva.",
        f"{voice_name_tts} qui, collegamento stabilito. Buona gara!",
    ]

    radio_dir = os.path.join(output_dir, f"voice/radio_check_{voice_name}")
    os.makedirs(radio_dir, exist_ok=True)

    for i, phrase in enumerate(radio_phrases, 1):
        output_path = os.path.join(radio_dir, f"{i}.wav")
        if os.path.exists(output_path):
            continue

        temp_path = output_path + ".tmp.wav"
        if generate_audio(model, phrase, temp_path, speed):
            apply_audio_effects(temp_path, output_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.info(f"Radio check {i}/{len(radio_phrases)}: {phrase[:50]}")


def count_existing_files(output_dir: str) -> int:
    """Conta i file WAV gia generati nella directory di output."""
    count = 0
    for root, _, files in os.walk(output_dir):
        for f in files:
            if f.endswith(".wav"):
                count += 1
    return count


def parse_arguments() -> argparse.Namespace:
    """Analizza gli argomenti da riga di comando."""
    parser = argparse.ArgumentParser(
        description="Genera voice pack italiani per CrewChief V4 usando XTTS v2."
    )
    parser.add_argument(
        "--config",
        default="./voice_generator/voices_config.yaml",
        help="Percorso al file di configurazione voci (default: ./voice_generator/voices_config.yaml)",
    )
    parser.add_argument(
        "--phrase-inventory",
        default="./lexicon/phrase_inventory_ita.csv",
        help="Percorso al phrase inventory italiano (default: ./lexicon/phrase_inventory_ita.csv)",
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Directory di output (default: ./output)",
    )
    parser.add_argument(
        "--voice",
        default=None,
        help="Genera solo questa voce (default: tutte)",
    )
    parser.add_argument(
        "--cpu-only",
        action="store_true",
        help="Usa solo CPU (piu lento ma non richiede GPU NVIDIA)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Rigenera file esistenti",
    )
    parser.add_argument(
        "--variation-count",
        type=int,
        default=None,
        help="Numero varianti per frase (sovrascrive config)",
    )
    parser.add_argument(
        "--xtts-speed",
        type=float,
        default=None,
        help="Velocita TTS (sovrascrive config)",
    )
    parser.add_argument(
        "--skip-radio-check",
        action="store_true",
        help="Salta la generazione dei file radio check",
    )
    parser.add_argument(
        "--max-invalid-attempts",
        type=int,
        default=30,
        help="Tentativi massimi per generare un file valido (default: 30)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point principale per la generazione dei voice pack."""
    args = parse_arguments()

    # Carica configurazione
    config = load_config(args.config)
    voices_config = config.get("voices", {})
    gen_config = config.get("generation", {})

    if not voices_config:
        logger.error("Nessuna voce configurata in voices_config.yaml")
        sys.exit(1)

    # Filtra voce se specificata
    if args.voice:
        if args.voice not in voices_config:
            logger.error(f"Voce '{args.voice}' non trovata. Disponibili: {list(voices_config.keys())}")
            sys.exit(1)
        voices_config = {args.voice: voices_config[args.voice]}

    # Carica phrase inventory
    logger.info(f"Caricamento phrase inventory da {args.phrase_inventory}...")
    entries = load_phrase_inventory(args.phrase_inventory)
    logger.info(f"Caricate {len(entries)} frasi")

    if not entries:
        logger.error("Phrase inventory vuoto o non trovato")
        sys.exit(1)

    device = "cpu" if args.cpu_only else "cuda"

    # Genera per ogni voce
    for voice_name, voice_cfg in voices_config.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Generazione voce: {voice_name} - {voice_cfg.get('description', '')}")
        logger.info(f"{'='*60}")

        ref_audio_dir = voice_cfg.get("reference_audio", f"./reference_audio/{voice_name.lower()}/")
        language = voice_cfg.get("language", "it")
        speed = args.xtts_speed or voice_cfg.get("speed", 1.4)
        variation_count = args.variation_count if args.variation_count is not None else voice_cfg.get("variation_count", 2)

        voice_output_dir = os.path.join(args.output_dir, voice_name)

        # Conta file esistenti
        existing = count_existing_files(voice_output_dir)
        logger.info(f"File esistenti: {existing}")

        # Inizializza modello TTS
        model = init_tts_model(ref_audio_dir, language, device)

        # Genera file audio
        total_phrases = len(entries) * (1 + variation_count)
        skipped = 0
        generated = 0
        failed = 0

        # Randomizza ordine per distribuzione migliore con multi-istanza
        shuffled_entries = list(entries)
        random.shuffle(shuffled_entries)

        with tqdm(total=total_phrases, desc=f"Voce {voice_name}", unit="frase") as pbar:
            for entry in shuffled_entries:
                # Percorso audio: converti backslash Windows in forward slash
                audio_path = entry.audio_path.replace("\\", "/")
                base_filename = entry.audio_filename.replace(".wav", "")

                # File principale + varianti
                for var_idx in range(1 + variation_count):
                    if var_idx == 0:
                        filename = f"{base_filename}.wav"
                    else:
                        filename = f"{base_filename}-{chr(96 + var_idx)}.wav"

                    output_path = os.path.join(voice_output_dir, audio_path.lstrip("/"), filename)

                    # Salta se esiste e non sovrascrivere
                    if os.path.exists(output_path) and not args.overwrite:
                        skipped += 1
                        pbar.update(1)
                        continue

                    # Genera audio
                    temp_path = output_path + ".tmp.wav"
                    success = False

                    for attempt in range(args.max_invalid_attempts):
                        if generate_audio(model, entry.text_for_tts, temp_path, speed):
                            # Applica effetti audio
                            apply_audio_effects(temp_path, output_path)

                            # Valida risultato
                            if validate_wav(output_path, entry.text_for_tts):
                                success = True
                                break
                            else:
                                logger.debug(
                                    f"File non valido (tentativo {attempt + 1}): {output_path}"
                                )
                                if os.path.exists(output_path):
                                    os.remove(output_path)

                    # Cleanup temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    if success:
                        generated += 1
                    else:
                        failed += 1
                        logger.warning(
                            f"Impossibile generare: {output_path} "
                            f"(testo: '{entry.text_for_tts[:50]}')"
                        )

                    pbar.update(1)

        logger.info(
            f"\nVoce {voice_name} completata: "
            f"{generated} generati, {skipped} saltati, {failed} falliti"
        )

        # Genera radio check
        if not args.skip_radio_check:
            logger.info(f"Generazione radio check per {voice_name}...")
            voice_name_tts = voice_name  # Potrebbe essere personalizzato
            generate_radio_check(model, voice_name, voice_name_tts, voice_output_dir, speed)

        # Genera file spotter se configurato
        if voice_cfg.get("use_as_spotter", False):
            spotter_dir = os.path.join(voice_output_dir, f"voice/spotter_{voice_name}")
            os.makedirs(spotter_dir, exist_ok=True)
            logger.info(f"Voce {voice_name} configurata come spotter: {spotter_dir}")

    logger.info("\n" + "=" * 60)
    logger.info("Generazione completata!")
    logger.info(f"Output: {os.path.abspath(args.output_dir)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
