import re
from pathlib import Path

PROMPTS_FILE = Path("recording_prompts.md")
WAV_DIR = Path("finetune_dataset/female/wavs")
OUT = Path("finetune_dataset/female/metadata.csv")

expected = {}
for line in PROMPTS_FILE.read_text().splitlines():
    m = re.match(r"^(\d{3})\.\s+(.+)$", line.strip())
    if m and 1 <= int(m.group(1)) <= 40:
        expected[m.group(1)] = m.group(2)

lines, missing = [], []
for pid in sorted(expected):
    if (WAV_DIR / f"prompt_{pid}.wav").exists():
        lines.append(f"prompt_{pid}|{expected[pid]}|{expected[pid]}")
    else:
        missing.append(pid)

OUT.write_text("\n".join(lines) + "\n")
print(f"Wrote {len(lines)} lines to {OUT}")
if missing:
    print(f"No wav for: {missing}")
