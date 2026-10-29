import csv
import random
import re
from pathlib import Path
from english_common_prompts import common_en

WAVS_DIR = Path("finetune_dataset/male/wavs")
OUT_DIR = Path("finetune_dataset/male")
PROMPTS_FILE = Path("recording_prompts.md")

texts = {}
pattern = re.compile(r"^(\d{3})\.\s+(.+)$")
with open(PROMPTS_FILE) as f:
    for line in f:
        m = pattern.match(line.strip())
        if m:
            texts[f"prompt_{m.group(1)}"] = m.group(2)

for pid, text in common_en.items():
    texts[f"prompt_{pid}"] = text

rows = []
for utt_id, text in texts.items():
    wav_path = WAVS_DIR / f"{utt_id}.wav"
    if wav_path.exists():
        rows.append((f"wavs/{utt_id}.wav", text, "male_voice"))

print(f"Found {len(rows)} matched audio+text pairs")

random.seed(42)
random.shuffle(rows)
eval_count = max(5, int(len(rows) * 0.08))  # small held-out eval set
eval_rows = rows[:eval_count]
train_rows = rows[eval_count:]

for name, data in [("metadata_train.csv", train_rows), ("metadata_eval.csv", eval_rows)]:
    with open(OUT_DIR / name, "w", newline="") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerow(["audio_file", "text", "speaker_name"])
        writer.writerows(data)
    print(f"Wrote {len(data)} rows to {name}")
