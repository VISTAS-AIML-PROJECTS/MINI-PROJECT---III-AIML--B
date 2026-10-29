"""
prepare_dataset.py
Second half of Milestone 3: clean the raw audio and build train/val/test
manifests, split by HELD-OUT SPEAKER (not held-out utterance) so evaluation
actually tests generalization to unseen voices.

What it does to each clip:
  - Converts to mono (TORGO audio should already be mono, but enforced)
  - Resamples to 16kHz (SpeechT5's expected input rate)
  - Trims leading/trailing silence
  - Peak-normalizes volume
  - Drops clips that are too short (<0.5s) or too long (>15s) — outliers
    that tend to destabilize TTS training

Speaker split (15 total speakers: F01,F03,F04,FC01,FC02,FC03,
M01-M05,MC01-MC04):
  - test speakers held out completely: 1 healthy + 1 dysarthric
  - val speakers held out completely: 1 healthy + 1 dysarthric
  - everyone else -> train

Output:
    data/processed/
    ├── wavs/                  # cleaned .wav files, 16kHz mono
    ├── train_manifest.csv
    ├── val_manifest.csv
    └── test_manifest.csv
Each manifest has columns: utterance_id, speaker_id, gender, speech_status, text

Usage:
    python prepare_dataset.py
"""

import os
import csv
import librosa
import soundfile as sf
import numpy as np

RAW_DIR = "data/raw"
RAW_WAV_DIR = os.path.join(RAW_DIR, "wavs")
RAW_MANIFEST = os.path.join(RAW_DIR, "transcripts.csv")

OUT_DIR = "data/processed"
OUT_WAV_DIR = os.path.join(OUT_DIR, "wavs")

TARGET_SR = 16000
MIN_DURATION_S = 0.5
MAX_DURATION_S = 15.0

# Held out entirely for val/test — never seen during training.
# Picked one healthy (C) + one dysarthric speaker per split for both sexes
# where possible, to keep both splits balanced across speech_status.
VAL_SPEAKERS = {"FC01", "M05"}
TEST_SPEAKERS = {"MC04", "F04"}


def clean_audio(wav_path):
    """Load, mono, resample, trim silence, peak-normalize. Returns array or None if rejected."""
    audio, sr = librosa.load(wav_path, sr=None, mono=True)

    if sr != TARGET_SR:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)

    audio, _ = librosa.effects.trim(audio, top_db=30)

    duration = len(audio) / TARGET_SR
    if duration < MIN_DURATION_S or duration > MAX_DURATION_S:
        return None

    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.95

    return audio


def main():
    os.makedirs(OUT_WAV_DIR, exist_ok=True)

    rows = []
    with open(RAW_MANIFEST, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from raw manifest.")

    writers = {}
    files = {}
    for split in ("train", "val", "test"):
        path = os.path.join(OUT_DIR, f"{split}_manifest.csv")
        files[split] = open(path, "w", newline="")
        writers[split] = csv.writer(files[split])
        writers[split].writerow(["utterance_id", "speaker_id", "gender", "speech_status", "text"])

    counts = {"train": 0, "val": 0, "test": 0, "rejected": 0, "arraymic_skipped": 0}

    for row in rows:
        # headMic-only: arrayMic (far-field) recordings produce much worse
        # speaker embeddings and audio quality (confirmed via
        # test_mic_quality.py) -- skip them entirely.
        if row.get("mic_type") != "headMic":
            counts["arraymic_skipped"] += 1
            continue

        speaker_id = row["speaker_id"]
        if speaker_id in VAL_SPEAKERS:
            split = "val"
        elif speaker_id in TEST_SPEAKERS:
            split = "test"
        else:
            split = "train"

        raw_wav_path = os.path.join(RAW_WAV_DIR, f"{row['utterance_id']}.wav")
        if not os.path.exists(raw_wav_path):
            counts["rejected"] += 1
            continue

        cleaned = clean_audio(raw_wav_path)
        if cleaned is None:
            counts["rejected"] += 1
            continue

        out_wav_path = os.path.join(OUT_WAV_DIR, f"{row['utterance_id']}.wav")
        sf.write(out_wav_path, cleaned, TARGET_SR)

        writers[split].writerow([
            row["utterance_id"], speaker_id, row["gender"], row["speech_status"], row["text"]
        ])
        counts[split] += 1

    for f in files.values():
        f.close()

    print(f"Train: {counts['train']} | Val: {counts['val']} | Test: {counts['test']} | "
          f"Rejected: {counts['rejected']} | ArrayMic skipped: {counts['arraymic_skipped']}")
    print(f"Val speakers (held out): {sorted(VAL_SPEAKERS)}")
    print(f"Test speakers (held out): {sorted(TEST_SPEAKERS)}")
    print("Done.")


if __name__ == "__main__":
    main()
