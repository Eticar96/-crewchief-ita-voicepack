#!/usr/bin/env python3
"""Installa il voice pack Leonardo in CrewChief V4."""

import os
import shutil
import getpass
from pathlib import Path

ROOT = Path(__file__).parent.parent
SOURCE = ROOT / "output" / "Leonardo"

# Trova CrewChief
username = getpass.getuser()
CREWCHIEF = Path(f"C:/Users/{username}/AppData/Local/CrewChiefV4")

if not CREWCHIEF.exists():
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        CREWCHIEF = Path(local) / "CrewChiefV4"

if not CREWCHIEF.exists():
    print(f"ERRORE: CrewChief non trovato in {CREWCHIEF}")
    exit(1)

if not SOURCE.exists():
    print(f"ERRORE: output/Leonardo non trovato")
    exit(1)

print(f"Sorgente: {SOURCE}")
print(f"CrewChief: {CREWCHIEF}")

# Conta file
wav_files = list(SOURCE.rglob("*.wav"))
print(f"File WAV da installare: {len(wav_files)}")

if len(wav_files) == 0:
    print("Nessun file da installare!")
    exit(1)

# Cartelle destinazione
dest_alt = CREWCHIEF / "sounds" / "alt" / "Leonardo"
dest_voice = CREWCHIEF / "sounds" / "voice"

copied = 0
for wav in wav_files:
    rel = wav.relative_to(SOURCE)
    rel_str = str(rel).replace("\\", "/")

    if "spotter" in rel_str.lower():
        dest = dest_voice / rel
    elif "radio_check" in rel_str.lower():
        dest = dest_voice / rel
    else:
        dest = dest_alt / rel

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wav, dest)
    copied += 1

    if copied % 1000 == 0:
        print(f"  {copied}/{len(wav_files)} copiati...")

print(f"\nInstallazione completata: {copied} file copiati")
print(f"  Voce principale: {dest_alt}")
print(f"  Spotter/Radio: {dest_voice}")
print(f"\nApri CrewChief e seleziona 'Leonardo' dal menu voci.")
