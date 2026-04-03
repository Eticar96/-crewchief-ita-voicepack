#!/usr/bin/env python3
"""
Generator script to produce translations_dict.py
This creates the full Italian translation dictionary for CrewChief V4.
"""

import re

PYTHON = "/c/Users/utente/AppData/Local/Programs/Python/Python312/python.exe"

# Read input phrases
with open(r"C:\Users\utente\Documents\-crewchief-ita-voicepack\lexicon\phrases_to_translate.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Parse into categories
categories = []
current_cat = None
current_phrases = []

for line in lines:
    line = line.rstrip("\n").rstrip("\r")
    m = re.match(r"^=== (.+?) \((\d+)\) ===$", line)
    if m:
        if current_cat and current_phrases:
            categories.append((current_cat, list(current_phrases)))
        current_cat = m.group(1)
        current_phrases = []
    elif line.strip() == "":
        continue
    else:
        current_phrases.append(line)

if current_cat and current_phrases:
    categories.append((current_cat, list(current_phrases)))

total = sum(len(ps) for _, ps in categories)
print(f"Parsed {total} phrases in {len(categories)} categories")
for cat, ps in categories:
    print(f"  {cat}: {len(ps)}")
