import os, csv

jim = r'C:\Users\utente\AppData\Local\CrewChiefV4\sounds\voice'
leo = r'C:\Users\utente\AppData\Local\CrewChiefV4\sounds\alt\Leonardo\voice'

to_generate = []

for root, dirs, files in os.walk(leo):
    rel = os.path.relpath(root, leo)
    for f in files:
        if not f.endswith('.wav'):
            continue
        jim_path = os.path.join(jim, rel, f)
        leo_path = os.path.join(root, f)

        if os.path.exists(jim_path) and os.path.getsize(jim_path) == os.path.getsize(leo_path):
            sub_file = os.path.join(root, 'subtitles.csv')
            text = ''
            if os.path.exists(sub_file):
                with open(sub_file, 'r', encoding='utf-8', errors='ignore') as sf:
                    for line in sf:
                        parts = line.strip().split(',', 1)
                        if len(parts) == 2 and parts[0].strip().strip('"') == f:
                            text = parts[1].strip().strip('"')
                            break

            if text:
                audio_path = chr(92) + 'voice' + chr(92) + rel.replace(os.sep, chr(92))
                to_generate.append((audio_path, f, text, text))

out_path = r'C:\Users\utente\Documents\-crewchief-ita-voicepack\lexicon\regen_jim_replacements.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as out:
    w = csv.writer(out)
    w.writerow(['audio_path', 'audio_filename', 'subtitle', 'text_for_tts'])
    for row in to_generate:
        w.writerow(row)

print(f'File da generare con voce Leonardo: {len(to_generate)}')

areas = {}
for path, fname, text, tts in to_generate:
    area = path.replace(chr(92), '/').strip('/').replace('voice/', '').split('/')[0]
    areas[area] = areas.get(area, 0) + 1

for area, count in sorted(areas.items(), key=lambda x: -x[1])[:15]:
    print(f'  {area}: {count} file')

no_text = 898 - len(to_generate)
if no_text > 0:
    print(f'\n  File senza testo (subtitles mancanti): {no_text}')
