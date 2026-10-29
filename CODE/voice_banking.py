"""
voice_banking.py
Degradation-robust identity banking (Table I's "longitudinal comparison"
concept): tracks a speaker's voice embedding across multiple recording
sessions over time, and always favors the clips most similar to the
earliest ("baseline") session when selecting reference audio -- so voice
identity is preserved even as later recordings may drift (fatigue,
illness progression, recording conditions, etc.), rather than just using
whatever was recorded most recently.

Usage:
    python voice_banking.py bootstrap male
    python voice_banking.py add male /path/to/new_session_folder session_label
    python voice_banking.py report male
"""

import os
import sys
import json
import shutil
import glob
from datetime import date

import torch
from extract_patient_embedding import extract_embedding

BANK_DIR = "voice_bank"


def _voice_dir(voice):
    return os.path.join(BANK_DIR, voice)


def _manifest_path(voice):
    return os.path.join(_voice_dir(voice), "manifest.json")


def _load_manifest(voice):
    path = _manifest_path(voice)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"clips": []}


def _save_manifest(voice, manifest):
    os.makedirs(_voice_dir(voice), exist_ok=True)
    with open(_manifest_path(voice), "w") as f:
        json.dump(manifest, f, indent=2)


def _embed_and_register(voice, session, wav_path, is_baseline):
    """Computes and caches the embedding for one clip, adds it to the manifest."""
    session_dir = os.path.join(_voice_dir(voice), session)
    os.makedirs(session_dir, exist_ok=True)

    dest_wav = os.path.join(session_dir, os.path.basename(wav_path))
    if os.path.abspath(dest_wav) != os.path.abspath(wav_path):
        shutil.copy2(wav_path, dest_wav)

    embedding = extract_embedding(dest_wav)
    emb_path = dest_wav.replace(".wav", "_embedding.pt")
    torch.save(embedding, emb_path)

    manifest = _load_manifest(voice)
    manifest["clips"].append({
        "session": session,
        "wav_path": dest_wav,
        "embedding_path": emb_path,
        "date": str(date.today()),
        "is_baseline": is_baseline,
    })
    _save_manifest(voice, manifest)
    return embedding


def bootstrap(voice, source_clips=None):
    """One-time: seed the baseline session from the voice's existing best
    reference clips (your earliest, healthiest recordings)."""
    if source_clips is None:
        source_clips = [
            f"finetune_dataset/{voice}/wavs/prompt_029.wav",
            f"finetune_dataset/{voice}/wavs/prompt_047.wav",
        ]
    existing = [p for p in source_clips if os.path.exists(p)]
    if not existing:
        print(f"No source clips found for '{voice}' -- nothing to bootstrap.")
        return

    for clip in existing:
        print(f"  Embedding baseline clip: {clip}")
        _embed_and_register(voice, "baseline", clip, is_baseline=True)
    print(f"Bootstrapped baseline for '{voice}' with {len(existing)} clip(s).")


def add_session(voice, folder, label):
    """Adds a new recording session (a folder of .wav files) to the bank,
    tagged with a date and label -- NOT marked as baseline."""
    wav_files = sorted(glob.glob(os.path.join(folder, "*.wav")))
    if not wav_files:
        print(f"No .wav files found in {folder}")
        return
    for wav in wav_files:
        print(f"  Embedding session clip: {wav}")
        _embed_and_register(voice, label, wav, is_baseline=False)
    print(f"Added session '{label}' for '{voice}' with {len(wav_files)} clip(s).")


def _baseline_embedding(voice):
    manifest = _load_manifest(voice)
    baseline_embs = [
        torch.load(c["embedding_path"], weights_only=False)
        for c in manifest["clips"] if c["is_baseline"]
    ]
    if not baseline_embs:
        return None
    return torch.stack(baseline_embs).mean(dim=0)


def _similarity(a, b):
    return torch.nn.functional.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0)).item()


def drift_report(voice):
    """Returns a list of {session, date, avg_similarity} for every
    non-baseline session, sorted chronologically."""
    baseline_emb = _baseline_embedding(voice)
    if baseline_emb is None:
        return []

    manifest = _load_manifest(voice)
    sessions = {}
    for c in manifest["clips"]:
        if c["is_baseline"]:
            continue
        emb = torch.load(c["embedding_path"], weights_only=False)
        sim = _similarity(emb, baseline_emb)
        sessions.setdefault(c["session"], {"date": c["date"], "sims": []})
        sessions[c["session"]]["sims"].append(sim)

    report = []
    for session, info in sessions.items():
        avg_sim = sum(info["sims"]) / len(info["sims"])
        report.append({"session": session, "date": info["date"], "avg_similarity": round(avg_sim, 4)})

    return sorted(report, key=lambda r: r["date"])


def weighted_references(voice, n=2):
    """Returns up to n clip paths, ranked by similarity to the baseline
    embedding -- the clips most representative of the speaker's original,
    healthiest voice. Falls back to None if no bank exists yet (caller
    should fall back to its own default reference clips)."""
    baseline_emb = _baseline_embedding(voice)
    if baseline_emb is None:
        return None

    manifest = _load_manifest(voice)
    scored = []
    for c in manifest["clips"]:
        emb = torch.load(c["embedding_path"], weights_only=False)
        sim = _similarity(emb, baseline_emb)
        scored.append((sim, c["wav_path"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [path for _, path in scored[:n]] or None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cmd, voice = sys.argv[1], sys.argv[2]

    if cmd == "bootstrap":
        bootstrap(voice)
    elif cmd == "add":
        folder, label = sys.argv[3], sys.argv[4]
        add_session(voice, folder, label)
    elif cmd == "report":
        report = drift_report(voice)
        if not report:
            print(f"No sessions recorded yet for '{voice}' (or no baseline set).")
        else:
            print(f"Drift report for '{voice}':")
            for r in report:
                flag = "  <-- notable drift" if r["avg_similarity"] < 0.75 else ""
                print(f"  [{r['date']}] {r['session']}: similarity={r['avg_similarity']}{flag}")
    else:
        print(f"Unknown command: {cmd}")
