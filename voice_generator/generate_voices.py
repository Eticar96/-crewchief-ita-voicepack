#!/usr/bin/env python3
"""Generatore voice pack italiani per CrewChief V4.

Usa Coqui XTTS v2 (API diretta model.inference) con sistema a 4 livelli
di temperature, post-processing professionale (pedalboard + noisereduce),
e validazione automatica con retry.
"""

import argparse
import csv
import logging
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import yaml
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Monkey-patch torchaudio.load per Windows (evita torchcodec/FFmpeg DLL)
# ---------------------------------------------------------------------------
def _patch_torchaudio():
    try:
        import torchaudio
        _orig = torchaudio.load
        def _sf_load(filepath, *a, **kw):
            try:
                data, sr = sf.read(str(filepath), dtype="float32")
                t = torch.from_numpy(data)
                if t.ndim == 1:
                    t = t.unsqueeze(0)
                else:
                    t = t.T
                return t, sr
            except Exception:
                return _orig(filepath, *a, **kw)
        torchaudio.load = _sf_load
    except ImportError:
        pass

_patch_torchaudio()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ===================================================================
# Sistema a 4 livelli
# ===================================================================

@dataclass
class PhraseTuning:
    temperature: float
    speed: float
    level: str

# Cartelle foglia / parent per ogni livello
_SPOTTER_LEAVES = {
    "car_left", "car_right", "clear_left", "clear_right",
    "clear_inside", "clear_outside", "clear_all_round", "clear",
    "still_there", "three_wide_on_inside", "three_wide_on_outside",
    "three_wide_on_left", "three_wide_on_right", "hold_your_line",
}
_SPOTTER_PARENTS = {"spotter"}

_SWEAR_PARENTS = {"rants"}

_EMOTIVE_LEAVES = {
    "won_race", "podium_finish", "good_start", "ok_start",
    "green_green_green", "get_ready",
    "overtaking", "being_overtaken", "being_held_up", "being_pressured",
    "must_do_better", "keep_it_up", "neutral",
    "push_to_get_win", "push_to_get_second", "push_to_get_third",
    "push_to_improve", "push_to_hold_position", "pits_exit_clear",
    "bad_start", "terrible_start",
    "expected_position_win", "expected_position_win_mid_race",
    "finished_race", "finished_race_good_finish", "finished_race_last",
    "last_lap", "last_lap_top_three", "two_to_go_leading",
    "five_minutes_left_leading", "five_minutes_left_podium",
    "acknowledge_driver_is_ok",
    "well_done", "bad_luck", "come_on", "oh_dear",
}
_EMOTIVE_PARENTS = {
    "pearls_of_wisdom", "push_now", "position", "lap_counter",
    "pace_notes",
}

LEVEL_DEFAULTS = {
    "tecnico":      {"temperature": 0.5,  "speed": 1.0},
    "emotivo":      {"temperature": 0.85, "speed": 1.1},
    "spotter":      {"temperature": 0.5,  "speed": 1.15},
    "imprecazione": {"temperature": 0.8,  "speed": 1.1},
}


def classify_phrase(audio_path: str) -> str:
    parts = audio_path.replace("\\", "/").strip("/").split("/")
    leaf = parts[-1] if parts else ""
    parent = parts[-2] if len(parts) >= 2 else ""

    if parent in _SWEAR_PARENTS or "sweary" in leaf or "rants" in audio_path.lower():
        return "imprecazione"
    if leaf in _SPOTTER_LEAVES or parent in _SPOTTER_PARENTS:
        return "spotter"
    if leaf in _EMOTIVE_LEAVES or parent in _EMOTIVE_PARENTS:
        return "emotivo"
    return "tecnico"


def get_phrase_tuning(audio_path: str, voice_cfg: dict) -> PhraseTuning:
    level = classify_phrase(audio_path)
    d = LEVEL_DEFAULTS[level]
    overrides = voice_cfg.get(f"level_{level}", {})
    return PhraseTuning(
        temperature=overrides.get("temperature", d["temperature"]),
        speed=overrides.get("speed", d["speed"]),
        level=level,
    )


# ===================================================================
# Modello XTTS v2 — API diretta
# ===================================================================

@dataclass
class PhraseEntry:
    audio_path: str
    audio_filename: str
    subtitle: str
    text_for_tts: str


def load_phrase_inventory(csv_path: str) -> list[PhraseEntry]:
    entries: list[PhraseEntry] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 4:
                entries.append(PhraseEntry(*row[:4]))
    return entries


def _load_xtts_model(device: str = "cuda"):
    """Carica il modello XTTS v2 (senza embedding). Ritorna (model, use_gpu)."""
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    from TTS.utils.manage import ModelManager

    manager = ModelManager()
    model_path, _, _ = manager.download_model(
        "tts_models/multilingual/multi-dataset/xtts_v2"
    )
    model_dir = model_path if os.path.isdir(model_path) else os.path.dirname(model_path)

    use_gpu = device == "cuda" and torch.cuda.is_available()
    logger.info(f"Caricamento XTTS v2 da {model_dir} ({'GPU' if use_gpu else 'CPU'})...")

    config = XttsConfig()
    config.load_json(os.path.join(model_dir, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=model_dir)
    if use_gpu:
        model.cuda()

    return model


def _collect_ref_files(ref_dir: Path, prefix_filter: str | None = None) -> list[Path]:
    """Raccoglie file audio di reference, opzionalmente filtrati per prefisso."""
    ref_files = []
    for ext in ("*.wav", "*.mp3", "*.flac"):
        ref_files.extend(ref_dir.glob(ext))
    if prefix_filter:
        ref_files = [f for f in ref_files if f.stem.startswith(prefix_filter)]
    return sorted(ref_files)


def _compute_latents(model, ref_files, gpt_cond_len, gpt_cond_chunk_len, max_ref_length):
    """Calcola gpt_cond_latent e speaker_embedding da una lista di file."""
    return model.get_conditioning_latents(
        audio_path=[str(f) for f in ref_files],
        gpt_cond_len=gpt_cond_len,
        gpt_cond_chunk_len=gpt_cond_chunk_len,
        max_ref_length=max_ref_length,
    )


def init_model(
    reference_audio_dir: str,
    language: str = "it",
    device: str = "cuda",
    gpt_cond_len: int = 12,
    gpt_cond_chunk_len: int = 4,
    max_ref_length: int = 30,
    voice_cfg: dict | None = None,
) -> object:
    """Carica XTTS v2 e calcola voice embedding da tutti i file reference.

    Se voice_cfg ha block_conditioning=true, calcola latent separati per blocco
    (gpt_cond_latent diverso per tipo frase) e speaker_embedding medio da tutti.
    """
    model = _load_xtts_model(device)
    ref_dir = Path(reference_audio_dir)

    # Raccolta TUTTI i file reference (20-40 file supportati)
    all_ref_files = _collect_ref_files(ref_dir)
    if not all_ref_files:
        logger.error(f"Nessun file reference in {reference_audio_dir}")
        sys.exit(1)

    logger.info(f"Reference: {len(all_ref_files)} file, gpt_cond_len={gpt_cond_len}, "
                f"chunk_len={gpt_cond_chunk_len}, max_ref={max_ref_length}s")
    for f in all_ref_files:
        logger.info(f"  -> {f}")

    # Speaker embedding globale (media di TUTTI i clip — identita' vocale)
    gpt_cond_latent_all, speaker_embedding = _compute_latents(
        model, all_ref_files, gpt_cond_len, gpt_cond_chunk_len, max_ref_length,
    )

    model._gpt_cond_latent = gpt_cond_latent_all
    model._speaker_embedding = speaker_embedding
    model._language = language

    # Conditioning contestuale per blocco (Leonardo e voci con block_conditioning)
    model._block_latents = {}
    if voice_cfg and voice_cfg.get("block_conditioning"):
        blocks = voice_cfg.get("blocks", {})
        for block_id, block_cfg in blocks.items():
            prefix = block_cfg.get("prefix", "")
            phrase_type = block_cfg.get("type", "tecnico")
            block_files = _collect_ref_files(ref_dir, prefix_filter=prefix)
            if block_files:
                block_latent, _ = _compute_latents(
                    model, block_files, gpt_cond_len, gpt_cond_chunk_len, max_ref_length,
                )
                model._block_latents[phrase_type] = block_latent
                logger.info(f"  Blocco {block_id} ({phrase_type}): {len(block_files)} file -> latent cachato")
            else:
                logger.warning(f"  Blocco {block_id}: nessun file con prefisso '{prefix}', uso latent globale")

    logger.info(f"Modello pronto, embedding cachato"
                f" ({len(model._block_latents)} blocchi contestuali)" if model._block_latents else
                "Modello pronto, embedding cachato")
    return model


def get_block_latent(model, phrase_level: str):
    """Ritorna il gpt_cond_latent appropriato per il tipo di frase.

    Se ci sono latent per blocco e il tipo corrisponde, usa quello specifico.
    Altrimenti usa il latent globale (media di tutti i clip).
    """
    if model._block_latents and phrase_level in model._block_latents:
        return model._block_latents[phrase_level]
    return model._gpt_cond_latent


# ===================================================================
# Generazione audio — API diretta model.inference
# ===================================================================

# ===================================================================
# Dizionario correzione accenti italiani per TTS
# XTTS non distingue omografi italiani — aggiungiamo accenti espliciti
# sul testo per guidare la pronuncia corretta.
# Formato: "parola" -> "paròla" (con accento sulla sillaba tonica)
# ===================================================================

# Parole con accento SDRUCCIOLO (terzultima sillaba) o ambigue
# che XTTS tende a sbagliare nel contesto motorsport
_ACCENT_FIXES: dict[str, str] = {
    # Verbi imperativi (accento sulla radice, non sulla desinenza)
    "concentrati": "concèntrati",
    "preparati": "prepàrati",
    "calmati": "càlmati",
    "rilassati": "rilàssati",
    "fermati": "fèrmati",
    "spostati": "spòstati",
    "rimettiti": "rimèttiti",
    "riprenditi": "riprènditi",
    "difenditi": "difènditi",
    "ricordati": "ricòrdati",
    "svegliati": "svègliati",

    # Verbi imperativi - seconda persona singolare
    "capitano": "càpitano",  # "capita-no" (succedono), non "capitàno"
    "perdere": "pèrdere",
    "prendere": "prèndere",
    "correre": "còrrere",
    "mettere": "méttere",
    "scendere": "scèndere",
    "spingere": "spìngere",
    "chiudere": "chiùdere",
    "muovere": "muòvere",
    "uscire": "uscìre",

    # Sostantivi/avverbi ambigui
    "ancora": "ancòra",       # "ancora" avverbio (= di nuovo), non àncora
    "subito": "sùbito",       # "subito" avverbio (= immediatamente)
    "principi": "princìpi",   # "principi" (= regole), non prìncipi (= nobili)
    "compito": "còmpito",     # "compito" (= task), non compìto (= educato)
    "circuito": "circùito",   # circuito di gara
    "arbitro": "àrbitro",
    "limite": "lìmite",
    "obbligo": "òbbligo",
    # Participi passati ambigui
    "deciso": "decìso",
    "previsto": "prevìsto",
    "compreso": "comprèso",

    # Parole motorsport specifiche
    "settore": "settóre",
    "anteriore": "anterióre",
    "posteriore": "posterióre",
    "sospensione": "sospensióne",
    "traiettoria": "traiettòria",
    "carrozzeria": "carrozzerìa",

    # Congiunzioni/avverbi che XTTS pronuncia male
    "pero'": "però",
    "perche'": "perché",
    "cioe'": "cioè",
    "piu'": "più",
    "gia'": "già",
    "cosi'": "così",
    "sara'": "sarà",
    "fara'": "farà",
    "dovra'": "dovrà",
    "potra'": "potrà",
    "avra'": "avrà",
    "terra'": "terrà",
    "dara'": "darà",
    "andra'": "andrà",
    "verra'": "verrà",
    "stara'": "starà",
    "si'": "sì",
    "e'": "è",

    # Parole comuni con accento ambiguo — ENTRAMBE le forme (con e senza apostrofo)
    "meta'": "metà", "meta": "metà",
    "citta'": "città", "citta": "città",
    "qualita'": "qualità", "qualita": "qualità",
    "capacita'": "capacità", "capacita": "capacità",
    "possibilita'": "possibilità", "possibilita": "possibilità",
    "necessita'": "necessità", "necessita": "necessità",
    "liberta'": "libertà", "liberta": "libertà",
    "difficolta'": "difficoltà", "difficolta": "difficoltà",
    "opportunita'": "opportunità", "opportunita": "opportunità",
    "penalita'": "penalità", "penalita": "penalità",
    "velocita'": "velocità", "velocita": "velocità",
    "stabilita'": "stabilità", "stabilita": "stabilità",
    "visibilita'": "visibilità", "visibilita": "visibilità",
    "umidita'": "umidità", "umidita": "umidità",
    "probabilita'": "probabilità", "probabilita": "probabilità",

    # Verbi comuni accentati — ENTRAMBE le forme
    "puo'": "può", "puo": "può",
    "dovro'": "dovrò", "dovro": "dovrò",
    "potro'": "potrò", "potro": "potrò",
    "andro'": "andrò", "andro": "andrò",
    "faro'": "farò", "faro": "farò",
    "saro'": "sarò", "saro": "sarò",
    "vedro'": "vedrò", "vedro": "vedrò",
    "avro'": "avrò", "avro": "avrò",
    "terro'": "terrò", "terro": "terrò",
    "vorro'": "vorrò", "vorro": "vorrò",
    "sara'": "sarà", "sara": "sarà",
    "fara'": "farà", "fara": "farà",
    "dovra'": "dovrà", "dovra": "dovrà",
    "potra'": "potrà", "potra": "potrà",
    "avra'": "avrà", "avra": "avrà",
    "terra'": "terrà", "terra": "terrà",
    "dara'": "darà", "dara": "darà",
    "andra'": "andrà", "andra": "andrà",
    "verra'": "verrà", "verra": "verrà",
    "stara'": "starà", "stara": "starà",

    # Motorsport — accenti specifici
    "degrado": "degràdo",
    "consumate": "consumàte",
    "bilanciamento": "bilanciamènto",
    "surriscaldati": "surriscaldàti",
    "surriscaldamento": "surriscaldamènto",
    "rifornimento": "rifornimènto",
    "piazzamento": "piazzamènto",
    "campionato": "campionàto",
    "traguardo": "traguàrdo",
    "sorpasso": "sorpàsso",
    "distacco": "distàcco",
    "vantaggio": "vantàggio",
    "svantaggio": "svantàggio",
    "margine": "màrgine",

    # Aggettivi che XTTS confonde
    "fantastica": "fantàstica",
    "fantastico": "fantàstico",
    "incredibile": "incredìbile",
    "terribile": "terrìbile",
    "possibile": "possìbile",
    "impossibile": "impossìbile",
    "disponibile": "disponìbile",
    "significativa": "significatìva",
    "significativo": "significatìvo",

    # Numeri ordinali
    "dodicesimo": "dodicèsimo",
    "tredicesimo": "tredicèsimo",
    "quattordicesimo": "quattordicèsimo",
    "quindicesimo": "quindicèsimo",
    "sedicesimo": "sedicèsimo",
    "diciassettesimo": "diciassettèsimo",
    "diciottesimo": "diciottèsimo",
    "diciannovesimo": "diciannovèsimo",
    "ventesimo": "ventèsimo",

    # Avverbi
    "immediatamente": "immediatamènte",
    "completamente": "completamènte",
    "facilmente": "facilmènte",
    "probabilmente": "probabilmènte",
    "sicuramente": "sicuramènte",
    "evidentemente": "evidentemènte",
    "davvero": "davvéro",
    "adesso": "adèsso",
}

import re as _re

def _apply_accent_fixes(text: str) -> str:
    """Applica le correzioni di accento al testo per TTS."""
    result = text
    for wrong, fixed in _ACCENT_FIXES.items():
        # Match parola intera, case-insensitive, preserva case originale
        pattern = _re.compile(r'\b' + _re.escape(wrong) + r'\b', _re.IGNORECASE)
        result = pattern.sub(fixed, result)
    return result


def prepare_text(text: str) -> str:
    """Prepara il testo per XTTS: accenti + punti -> !"""
    t = text.strip()
    t = _apply_accent_fixes(t)
    t = t.replace(". ", "! ").rstrip(".")
    if t and t[-1] not in ("!", "?", ","):
        t += "!"
    return t


def generate_audio(
    model: object,
    text: str,
    output_path: str,
    temperature: float = 0.5,
    speed: float = 1.0,
    seed: int | None = None,
    phrase_level: str = "tecnico",
) -> bool:
    """Genera WAV con model.inference. Usa latent contestuale se disponibile."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if seed is not None:
            torch.manual_seed(seed)

        prepared = prepare_text(text)

        # Frasi corte (<15 parole): text_splitting causa pause innaturali
        # Frasi lunghe (>=15 parole): text_splitting evita troncamento
        word_count = len(prepared.split())
        use_splitting = word_count >= 15

        # Se il testo ha ripetizioni intenzionali (spingi spingi, vai vai)
        # abbassa repetition_penalty per non penalizzarle
        words_lower = prepared.lower().split()
        has_repetition = len(words_lower) != len(set(words_lower))
        rep_penalty = 2.0 if has_repetition else 5.0

        # Latent contestuale: usa il blocco appropriato se disponibile
        gpt_cond = get_block_latent(model, phrase_level)

        out = model.inference(
            prepared,
            model._language,
            gpt_cond,
            model._speaker_embedding,
            temperature=temperature,
            speed=speed,
            length_penalty=1.0,
            repetition_penalty=rep_penalty,
            top_k=50,
            top_p=0.85,
            enable_text_splitting=use_splitting,
        )

        wav = out["wav"]
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        wav = np.asarray(wav, dtype=np.float32)

        if len(wav) < 100:
            return False

        sf.write(output_path, wav, 24000, subtype="PCM_16")
        return True

    except Exception as e:
        logger.warning(f"Generazione fallita per '{text[:40]}': {e}")
        return False


# ===================================================================
# Post-processing professionale
# ===================================================================

def postprocess(input_path: str, output_path: str, radio_fx: bool = False) -> bool:
    """Pipeline post-processing: noisereduce + pedalboard + loudnorm."""
    import noisereduce as nr
    import pyloudnorm as pyln
    from pedalboard import (
        Compressor, Gain, HighpassFilter, Limiter, Pedalboard,
    )

    try:
        audio, sr = sf.read(input_path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # --- 0. Se skip_postprocessing: solo resample a 22050 ---
        if os.environ.get("SKIP_POSTPROC") == "1":
            if sr != 22050:
                from scipy.signal import resample as scipy_resample
                n_samples = int(len(audio) * 22050 / sr)
                audio = scipy_resample(audio, n_samples).astype(np.float32)
            audio = np.clip(audio, -1.0, 1.0).astype(np.float32)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            sf.write(output_path, audio, 22050, subtype="PCM_16")
            return True

        # --- 1. Noise reduction (stazionario, leggero) ---
        audio = nr.reduce_noise(
            y=audio, sr=sr,
            stationary=True,
            prop_decrease=0.6,
        ).astype(np.float32)

        # --- 2. Trim SOLO silenzio puro (top_db=50, molto conservativo) ---
        # top_db=50 taglia solo silenzio quasi totale, NON tocca il parlato
        import librosa
        audio_trimmed, trim_idx = librosa.effects.trim(audio, top_db=50)
        if len(audio_trimmed) > int(sr * 0.05):
            # Margine di sicurezza: 150ms prima, 250ms dopo
            start_idx = trim_idx[0]
            end_idx = trim_idx[1]
            safe_start = max(0, start_idx - int(sr * 0.15))
            safe_end = min(len(audio), end_idx + int(sr * 0.25))
            audio = audio[safe_start:safe_end]

        # --- 3. Pedalboard: HP, compressor, gain, limiter (NO noise gate) ---
        # Niente noise gate — taglia le consonanti deboli a inizio/fine frase
        board = Pedalboard([
            HighpassFilter(cutoff_frequency_hz=80.0),
            Compressor(
                threshold_db=-26.0,
                ratio=3.0,
                attack_ms=2.0,
                release_ms=15.0,
            ),
            Gain(gain_db=6.0),
            Limiter(threshold_db=-1.0),
        ])
        # pedalboard vuole (channels, samples)
        audio_2d = audio[np.newaxis, :]
        audio_2d = board(audio_2d, sr)
        audio = audio_2d[0]

        # --- 4. Effetto radio F1 (opzionale) ---
        if radio_fx:
            from pedalboard import LowpassFilter
            radio_board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=300.0),
                LowpassFilter(cutoff_frequency_hz=4000.0),
                Compressor(
                    threshold_db=-20.0,
                    ratio=10.0,
                    attack_ms=1.0,
                    release_ms=10.0,
                ),
                Gain(gain_db=3.0),
                Limiter(threshold_db=-1.0),
            ])
            audio_2d = audio[np.newaxis, :]
            audio_2d = radio_board(audio_2d, sr)
            audio = audio_2d[0]

        # --- 5. LUFS normalization a -16 ---
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(audio)
        if loudness > -70:  # solo se c'e' audio reale
            audio = pyln.normalize.loudness(audio, loudness, -16.0)

        # Clip finale
        audio = np.clip(audio, -1.0, 1.0).astype(np.float32)

        # --- 6. Resample a 22050Hz e salva ---
        if sr != 22050:
            from scipy.signal import resample as scipy_resample
            n_samples = int(len(audio) * 22050 / sr)
            audio = scipy_resample(audio, n_samples).astype(np.float32)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        sf.write(output_path, audio, 22050, subtype="PCM_16")
        return True

    except Exception as e:
        logger.warning(f"Post-processing fallito: {e}")
        # fallback: copia raw
        import shutil
        shutil.copy2(input_path, output_path)
        return True


# ===================================================================
# Validazione
# ===================================================================

def validate_wav(file_path: str) -> bool:
    """Scarta file <0.3s, >15s, con RMS troppo basso, o con pause interne >0.4s."""
    try:
        data, sr = sf.read(file_path, dtype="float32")
        duration = len(data) / sr

        if duration < 0.3 or duration > 15.0:
            return False

        # Verifica che ci sia parlato reale (RMS sopra -40dB)
        rms = np.sqrt(np.mean(data ** 2))
        if rms < 10 ** (-40.0 / 20.0):
            return False

        # Rileva pause interne troppo lunghe (>0.4s di silenzio nel mezzo)
        # Questo cattura i casi di text_splitting che crea buchi
        frame_ms = 20
        frame_len = int(sr * frame_ms / 1000)
        silence_thresh = 10 ** (-45.0 / 20.0)
        consecutive_silent = 0
        max_silent = 0

        for i in range(frame_len, len(data) - frame_len, frame_len):
            frame_rms = np.sqrt(np.mean(data[i:i + frame_len] ** 2))
            if frame_rms < silence_thresh:
                consecutive_silent += 1
                max_silent = max(max_silent, consecutive_silent)
            else:
                consecutive_silent = 0

        max_silence_s = max_silent * frame_ms / 1000
        if max_silence_s > 0.4:
            return False

        return True
    except Exception:
        return False


# ===================================================================
# Radio check
# ===================================================================

def generate_radio_check(model, voice_name, output_dir, radio_fx, seed_base):
    phrases = [
        f"Ciao, sono {voice_name}, il tuo ingegnere di pista! Mi ricevi?",
        f"Radio check, qui {voice_name}! Tutto funziona!",
        f"Prova radio, {voice_name} in linea! Siamo pronti!",
        f"Eccomi, sono {voice_name}! Comunicazione attiva!",
        f"{voice_name} qui, collegamento stabilito! Buona gara!",
    ]
    radio_dir = os.path.join(output_dir, f"voice/radio_check_{voice_name}")
    os.makedirs(radio_dir, exist_ok=True)

    for i, phrase in enumerate(phrases, 1):
        out_path = os.path.join(radio_dir, f"{i}.wav")
        if os.path.exists(out_path):
            continue
        tmp = out_path + ".tmp.wav"
        if generate_audio(model, phrase, tmp, temperature=0.5, speed=1.0,
                          seed=seed_base + i):
            postprocess(tmp, out_path, radio_fx=radio_fx)
            if os.path.exists(tmp):
                os.remove(tmp)
            logger.info(f"Radio check {i}/5: {phrase[:50]}")


# ===================================================================
# CLI
# ===================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Genera voice pack ITA per CrewChief.")
    p.add_argument("--config", default="./voice_generator/voices_config.yaml")
    p.add_argument("--phrase-inventory", default="./lexicon/phrase_inventory_ita.csv")
    p.add_argument("--output-dir", default="./output")
    p.add_argument("--voice", default=None)
    p.add_argument("--cpu-only", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--variation-count", type=int, default=None)
    p.add_argument("--skip-radio-check", action="store_true")
    p.add_argument("--radio-fx", action="store_true", help="Applica effetto radio F1")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--xtts-speed", type=float, default=None)
    return p.parse_args()


# ===================================================================
# Main
# ===================================================================

def main():
    args = parse_args()

    config = yaml.safe_load(open(args.config, encoding="utf-8"))
    voices_cfg = config.get("voices", {})
    if not voices_cfg:
        logger.error("Nessuna voce configurata")
        sys.exit(1)

    if args.voice:
        if args.voice not in voices_cfg:
            logger.error(f"Voce '{args.voice}' non trovata: {list(voices_cfg.keys())}")
            sys.exit(1)
        voices_cfg = {args.voice: voices_cfg[args.voice]}

    entries = load_phrase_inventory(args.phrase_inventory)
    logger.info(f"Caricate {len(entries)} frasi da {args.phrase_inventory}")
    if not entries:
        sys.exit(1)

    device = "cpu" if args.cpu_only else "cuda"

    for voice_name, vcfg in voices_cfg.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Voce: {voice_name} — {vcfg.get('description', '')}")
        logger.info(f"{'='*60}")

        ref_dir = vcfg.get("reference_audio", f"./reference_audio/{voice_name.lower()}/")
        language = vcfg.get("language", "it")
        gpt_cond_len = vcfg.get("gpt_cond_len", 12)
        gpt_cond_chunk_len = vcfg.get("gpt_cond_chunk_len", 4)
        max_ref_length = vcfg.get("max_ref_length", 30)
        var_count = args.variation_count if args.variation_count is not None else vcfg.get("variation_count", 2)
        radio_fx = args.radio_fx or vcfg.get("radio_fx", False)
        skip_postproc = vcfg.get("skip_postprocessing", False)
        base_temp_override = vcfg.get("base_temperature", None)

        if skip_postproc:
            os.environ["SKIP_POSTPROC"] = "1"
            logger.info("Post-processing DISATTIVATO (timbro fedele)")
        else:
            os.environ.pop("SKIP_POSTPROC", None)

        logger.info("Sistema 4 livelli:")
        for lvl, p in LEVEL_DEFAULTS.items():
            logger.info(f"  {lvl:14s}  temp={p['temperature']:.2f}  speed={p['speed']:.2f}")

        voice_out = os.path.join(args.output_dir, voice_name)

        model = init_model(
            ref_dir, language, device,
            gpt_cond_len=gpt_cond_len,
            gpt_cond_chunk_len=gpt_cond_chunk_len,
            max_ref_length=max_ref_length,
            voice_cfg=vcfg,
        )

        # Seed per riproducibilita'
        base_seed = args.seed
        torch.manual_seed(base_seed)

        total = len(entries) * (1 + var_count)
        generated = skipped = failed = 0

        shuffled = list(entries)
        random.seed(base_seed)
        random.shuffle(shuffled)

        with tqdm(total=total, desc=f"Voce {voice_name}", unit="frase") as pbar:
            for idx, entry in enumerate(shuffled):
                audio_path = entry.audio_path.replace("\\", "/")
                base_fn = entry.audio_filename.replace(".wav", "")

                tuning = get_phrase_tuning(entry.audio_path, vcfg)
                temp = base_temp_override if base_temp_override is not None else tuning.temperature
                spd = args.xtts_speed or tuning.speed

                for var_idx in range(1 + var_count):
                    fn = f"{base_fn}.wav" if var_idx == 0 else f"{base_fn}-{chr(96+var_idx)}.wav"
                    out_path = os.path.join(voice_out, audio_path.lstrip("/"), fn)

                    if os.path.exists(out_path) and not args.overwrite:
                        skipped += 1
                        pbar.update(1)
                        continue

                    tmp = out_path + ".tmp.wav"
                    success = False
                    phrase_seed = base_seed + idx * 100 + var_idx

                    for attempt in range(3):
                        attempt_seed = phrase_seed + attempt * 7
                        if generate_audio(model, entry.text_for_tts, tmp,
                                          temperature=temp, speed=spd,
                                          seed=attempt_seed,
                                          phrase_level=tuning.level):
                            postprocess(tmp, out_path, radio_fx=radio_fx)
                            if validate_wav(out_path):
                                success = True
                                break
                            else:
                                logger.debug(f"Validazione fallita (try {attempt+1}): {out_path}")
                                if os.path.exists(out_path):
                                    os.remove(out_path)

                    if os.path.exists(tmp):
                        os.remove(tmp)

                    if success:
                        generated += 1
                    else:
                        failed += 1
                        logger.warning(
                            f"SKIP dopo 3 tentativi: [{tuning.level}] "
                            f"'{entry.text_for_tts[:40]}'"
                        )

                    pbar.update(1)

        logger.info(f"\n{voice_name}: {generated} OK, {skipped} saltati, {failed} falliti")

        if not args.skip_radio_check:
            generate_radio_check(model, voice_name, voice_out, radio_fx, base_seed)

        if vcfg.get("use_as_spotter", False):
            sp_dir = os.path.join(voice_out, f"voice/spotter_{voice_name}")
            os.makedirs(sp_dir, exist_ok=True)
            logger.info(f"Spotter dir: {sp_dir}")

    logger.info(f"\nCompletato! Output: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
