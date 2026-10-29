"""
orchestrate_pipeline_v2.py
THE real project's end-to-end pipeline, rebuilt on XTTS-v2:
  1. A real patient recording -> cleaned (noise reduction/trim/normalize)
     -> used DIRECTLY as XTTS's reference voice
  2. Text -> chunk_text()
  3. For each chunk: check quick_phrases first (real recording for known
     urgent phrases) -> falls back to synthesize_xtts.synthesize() (AI)
     for anything else
  4. All chunks -> stitch_audio.stitch() -> one final .wav

Usage:
    python orchestrate_pipeline_v2.py \
        --recording recordings/loki/session_1.wav \
        --text "Hi, this is a test of the EchoGenesis voice system." \
        --out outputs/pipeline_final.wav
"""

import os
import argparse
import re
import librosa
import numpy as np
import soundfile as sf

from extract_patient_embedding import clean_recording
from stitch_audio import stitch
from src.inference.synthesize_xtts import synthesize, get_sample_rate
from quick_phrases import get_quick_phrase_audio, is_quick_phrase


def chunk_text(text, max_chunk_length=200):
    """
    Splits text at sentence/clause punctuation, greedily packing pieces
    up to max_chunk_length.
    """
    raw_pieces = re.split(r'(?<=[.,;!?])\s+', text.strip())
    chunks = []
    current_chunk = ""
    for piece in raw_pieces:
        if len(current_chunk) + len(piece) <= max_chunk_length:
            current_chunk = (current_chunk + " " + piece).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = piece
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def prepare_reference_audio(recording_path, target_sr=16000):
    """Load, clean (noise reduce/trim/normalize), and save temp reference
    clip(s) ready for XTTS. Accepts either a single path (str) or a list
    of paths -- multiple clips give XTTS's speaker encoder a richer signal
    of the target voice.

    Returns: a single path (str) if given one input, or a list of paths
    if given multiple -- matching synthesize_xtts.synthesize()'s expected
    input shape either way.
    """
    paths = [recording_path] if isinstance(recording_path, str) else list(recording_path)
    os.makedirs("outputs", exist_ok=True)

    out_paths = []
    for i, p in enumerate(paths):
        audio, sr = librosa.load(p, sr=None, mono=True)
        if sr != target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        audio = clean_recording(audio, target_sr)

        temp_path = f"outputs/_temp_reference_{i}.wav"
        sf.write(temp_path, audio, samplerate=target_sr)
        out_paths.append(temp_path)

    return out_paths[0] if len(out_paths) == 1 else out_paths


def synthesize_with_quick_phrase_check(text, reference_path, voice="male", language="en", register=None):
    """
    Checks if this exact text matches a known emergency/common phrase for
    this voice+language+register (uses the REAL recording if so -- more
    reliable/authentic than AI). Falls back to AI synthesis only for
    English, since that's the only language with a trained voice model
    so far -- returns None for other languages with no quick-phrase
    match, signaling "AI speech not available yet" to the caller.
    """
    if is_quick_phrase(text, voice=voice, language=language, register=register):
        print(f"    -> using REAL recording (quick phrase match, voice={voice}, language={language}, register={register})")
        audio = get_quick_phrase_audio(text, voice=voice, language=language, register=register)
        if audio is not None:
            return audio

    if language != "en":
        print(f"    -> no AI voice model available yet for language={language}")
        return None

    print(f"    -> using AI synthesis (voice={voice})")
    return synthesize(text, speaker_wav_path=reference_path, voice=voice)


def run_pipeline(recording_path, text, out_path, max_chunk_length=200, keep_chunks=False, voice="male"):
    print(f"=== Step 1: preparing reference voice from {recording_path} ===")
    reference_path = prepare_reference_audio(recording_path)

    print(f"\n=== Step 2: chunking text ===")
    chunks = chunk_text(text, max_chunk_length=max_chunk_length)
    print(f"  split into {len(chunks)} chunk(s):")
    for i, c in enumerate(chunks, 1):
        print(f"    [{i}] \"{c}\"")

    print(f"\n=== Step 3: synthesizing each chunk (quick-phrase check + XTTS-v2) ===")
    sample_rate = get_sample_rate()
    chunk_audio = []
    chunk_dir = os.path.join(os.path.dirname(out_path) or ".", "pipeline_chunks")
    if keep_chunks:
        os.makedirs(chunk_dir, exist_ok=True)

    for i, chunk in enumerate(chunks, 1):
        print(f"  processing chunk {i}/{len(chunks)}: \"{chunk[:50]}...\"")
        audio = synthesize_with_quick_phrase_check(chunk, reference_path, voice=voice)
        chunk_audio.append(audio)
        if keep_chunks:
            sf.write(os.path.join(chunk_dir, f"chunk_{i:03d}.wav"), audio, samplerate=sample_rate)

    print(f"\n=== Step 4: stitching {len(chunk_audio)} chunks into final audio ===")
    final_audio = stitch(chunk_audio, sample_rate=sample_rate)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    sf.write(out_path, final_audio, samplerate=sample_rate)
    print(f"\nDone. Wrote {out_path} ({len(final_audio)/sample_rate:.2f}s total)")
    if keep_chunks:
        print(f"Individual chunks also saved to {chunk_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recording", required=True, help="Path to a real patient voice recording")
    parser.add_argument("--text", required=True, help="Full text to synthesize")
    parser.add_argument("--out", required=True, help="Final output .wav path")
    parser.add_argument("--max-chunk-length", type=int, default=200)
    parser.add_argument("--keep-chunks", action="store_true", help="Also save individual chunk .wav files")
    parser.add_argument("--voice", choices=["male", "female"], default="male", help="Which voice set to use for quick phrases")
    args = parser.parse_args()

    run_pipeline(args.recording, args.text, args.out, args.max_chunk_length, args.keep_chunks, voice=args.voice)
