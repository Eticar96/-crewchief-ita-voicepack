"""
Analyze WAV files in Leonardo voice pack for audio quality issues.
Scans ~27000 files efficiently using only stdlib modules.
"""

import wave
import struct
import os
import math
import sys
import time

BASE_DIR = r"C:\Users\utente\Documents\-crewchief-ita-voicepack\output\Leonardo"
OUTPUT_FILE = r"C:\Users\utente\Documents\-crewchief-ita-voicepack\output\Leonardo_audio_issues.txt"

# Thresholds
CLIPPING_THRESHOLD = 32000       # |sample| above this = clipping
CLIPPING_PERCENT_LIMIT = 1.0     # more than 1% clipped = problem
RMS_LOW_DB = -45.0               # below this = too quiet
RMS_HIGH_DB = -8.0               # above this = too loud
MAX_DURATION = 30.0              # seconds
EXPECTED_RATE = 22050
EXPECTED_BITS = 16
EXPECTED_CHANNELS = 1
SILENCE_THRESHOLD = 500          # |sample| below this = silence
SILENCE_RATIO_LIMIT = 0.70       # more than 70% silence = problem

issues = {
    "corrupted": [],
    "clipping": [],
    "volume_low": [],
    "volume_high": [],
    "duration_zero": [],
    "duration_long": [],
    "format_rate": [],
    "format_bits": [],
    "format_channels": [],
    "silence_ratio": [],
}


def rms_to_db(rms_val):
    if rms_val <= 0:
        return -100.0
    # Reference: max 16-bit = 32768
    return 20.0 * math.log10(rms_val / 32768.0)


def analyze_wav(filepath, relpath):
    """Analyze a single WAV file. Returns list of (issue_type, detail_str)."""
    found = []

    try:
        wf = wave.open(filepath, 'rb')
    except Exception as e:
        found.append(("corrupted", f"Cannot open: {e}"))
        return found

    try:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()

        # Format checks
        if framerate != EXPECTED_RATE:
            found.append(("format_rate", f"Sample rate: {framerate} Hz (expected {EXPECTED_RATE})"))
        if sampwidth != 2:  # 2 bytes = 16-bit
            found.append(("format_bits", f"Bit depth: {sampwidth*8}-bit (expected {EXPECTED_BITS})"))
        if nchannels != EXPECTED_CHANNELS:
            found.append(("format_channels", f"Channels: {nchannels} (expected {EXPECTED_CHANNELS})"))

        # Duration check
        if nframes == 0 or framerate == 0:
            found.append(("duration_zero", "Duration: 0 seconds (empty file)"))
            wf.close()
            return found

        duration = nframes / float(framerate)
        if duration > MAX_DURATION:
            found.append(("duration_long", f"Duration: {duration:.1f}s (max {MAX_DURATION}s)"))

        # Only do sample-level analysis for 16-bit mono/stereo
        if sampwidth != 2:
            wf.close()
            return found

        # Read all frames
        raw = wf.readframes(nframes)
        wf.close()

        total_samples = len(raw) // 2
        if total_samples == 0:
            found.append(("duration_zero", "No audio samples"))
            return found

        # Unpack samples
        samples = struct.unpack(f'<{total_samples}h', raw)

        # If stereo, just take every other sample (left channel) for speed
        if nchannels == 2:
            samples = samples[::2]

        n = len(samples)
        if n == 0:
            return found

        # Compute stats in one pass
        sum_sq = 0.0
        clip_count = 0
        silence_count = 0

        for s in samples:
            abs_s = abs(s)
            sum_sq += s * s
            if abs_s > CLIPPING_THRESHOLD:
                clip_count += 1
            if abs_s < SILENCE_THRESHOLD:
                silence_count += 1

        # Clipping
        clip_pct = (clip_count / n) * 100.0
        if clip_pct > CLIPPING_PERCENT_LIMIT:
            found.append(("clipping", f"Clipping: {clip_pct:.2f}% samples above |{CLIPPING_THRESHOLD}|"))

        # RMS volume
        rms = math.sqrt(sum_sq / n)
        rms_db = rms_to_db(rms)
        if rms_db < RMS_LOW_DB:
            found.append(("volume_low", f"RMS: {rms_db:.1f} dB (threshold {RMS_LOW_DB} dB)"))
        elif rms_db > RMS_HIGH_DB:
            found.append(("volume_high", f"RMS: {rms_db:.1f} dB (threshold {RMS_HIGH_DB} dB)"))

        # Silence ratio
        silence_ratio = silence_count / n
        if silence_ratio > SILENCE_RATIO_LIMIT:
            found.append(("silence_ratio", f"Silence: {silence_ratio*100:.1f}% (threshold {SILENCE_RATIO_LIMIT*100:.0f}%)"))

        return found

    except Exception as e:
        try:
            wf.close()
        except:
            pass
        found.append(("corrupted", f"Error reading data: {e}"))
        return found


def main():
    print(f"Scanning WAV files in: {BASE_DIR}")
    print(f"Output report: {OUTPUT_FILE}")
    print()

    # Collect all WAV files
    wav_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        for f in files:
            if f.lower().endswith('.wav'):
                wav_files.append(os.path.join(root, f))

    total = len(wav_files)
    print(f"Found {total} WAV files. Analyzing...")
    print()

    start_time = time.time()
    problem_files = 0
    all_issues_list = []  # (relpath, issue_type, detail)

    for i, fpath in enumerate(wav_files):
        relpath = os.path.relpath(fpath, BASE_DIR)

        file_issues = analyze_wav(fpath, relpath)

        if file_issues:
            problem_files += 1
            for issue_type, detail in file_issues:
                issues[issue_type].append((relpath, detail))
                all_issues_list.append((relpath, issue_type, detail))
                print(f"  [{issue_type.upper()}] {relpath} -- {detail}")

        # Progress every 5000 files
        if (i + 1) % 5000 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate
            print(f"  ... progress: {i+1}/{total} ({elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining)")

    elapsed = time.time() - start_time

    # Summary
    summary_lines = []
    summary_lines.append("=" * 70)
    summary_lines.append("RIEPILOGO ANALISI QUALITA AUDIO - Leonardo Voice Pack")
    summary_lines.append("=" * 70)
    summary_lines.append(f"File totali analizzati: {total}")
    summary_lines.append(f"File con problemi:      {problem_files}")
    summary_lines.append(f"Problemi totali:        {len(all_issues_list)}")
    summary_lines.append(f"Tempo di analisi:       {elapsed:.1f} secondi")
    summary_lines.append("")
    summary_lines.append("CONTEGGIO PER TIPO DI PROBLEMA:")
    summary_lines.append("-" * 50)

    type_labels = {
        "corrupted": "File corrotti",
        "clipping": "Clipping severo (>1% campioni)",
        "volume_low": "Volume troppo basso (<-45dB)",
        "volume_high": "Volume troppo alto (>-8dB)",
        "duration_zero": "Durata zero / file vuoto",
        "duration_long": "Durata eccessiva (>30s)",
        "format_rate": "Sample rate errato (!= 22050Hz)",
        "format_bits": "Bit depth errato (!= 16-bit)",
        "format_channels": "Canali errati (!= mono)",
        "silence_ratio": "Troppo silenzio (>70%)",
    }

    for key in issues:
        count = len(issues[key])
        label = type_labels.get(key, key)
        marker = " <<<" if count > 0 else ""
        summary_lines.append(f"  {label:45s} {count:6d}{marker}")

    summary_lines.append("")

    # Print details per category
    for key in issues:
        if issues[key]:
            label = type_labels.get(key, key)
            summary_lines.append(f"\n--- {label} ({len(issues[key])} file) ---")
            for relpath, detail in issues[key]:
                summary_lines.append(f"  {relpath}")
                summary_lines.append(f"    -> {detail}")

    summary_text = "\n".join(summary_lines)
    print()
    print(summary_text)

    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(summary_text)
        f.write("\n")

    print(f"\nReport salvato in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
