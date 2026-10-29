"""
synthesize.py
Milestone 6: the single clean entry point Person C (Module 5, chunking &
stitching) should import and call. Wraps model/vocoder/embedding loading
behind a cache so repeated calls are fast (loads once, not per-call).

Public function:
    synthesize(text: str, speaker_id: str | None = None,
               speaker_embedding: torch.Tensor | None = None) -> np.ndarray

    Pass EITHER speaker_id (looks up a precomputed embedding from
    embeddings/speaker_embeddings.pt) OR speaker_embedding directly (a
    512-dim tensor -- this is the slot Person A's real embedding plugs
    into once Sync Point 1 is resolved; format must match: 512-dim,
    x-vector style, matching speechbrain/spkrec-xvect-voxceleb convention).

    Returns: 1D numpy float32 array, 16kHz mono waveform. Caller (Person C)
    is responsible for chunking long text into sentences before calling
    this per the blueprint's pipeline split, and for stitching/saving.

Usage as a library:
    from src.inference.synthesize import synthesize
    audio = synthesize("Hello there.", speaker_id="MC04")

Usage as a quick CLI test:
    python src/inference/synthesize.py "Hello there." MC04
"""

import os
import torch
import numpy as np
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech

from src.inference.load_model import load_vocoder, get_device

CHECKPOINT_PATH = os.environ.get("ECHOGENESIS_CHECKPOINT", "checkpoints/epoch_33")
EMBEDDINGS_PATH = os.environ.get("ECHOGENESIS_EMBEDDINGS", "embeddings/speaker_embeddings.pt")

_cache = {}  # lazy-loaded singletons: model, processor, vocoder, device, speaker_embeddings


def _get_pipeline():
    if "model" not in _cache:
        device = get_device()
        _cache["device"] = device
        _cache["processor"] = SpeechT5Processor.from_pretrained(CHECKPOINT_PATH)
        _cache["model"] = SpeechT5ForTextToSpeech.from_pretrained(CHECKPOINT_PATH).to(device).eval()
        _cache["vocoder"] = load_vocoder().to(device).eval()
        _cache["speaker_embeddings"] = (
            torch.load(EMBEDDINGS_PATH) if os.path.exists(EMBEDDINGS_PATH) else {}
        )
    return _cache


def synthesize(text: str, speaker_id: str = None, speaker_embedding: torch.Tensor = None) -> np.ndarray:
    """
    Synthesize one utterance of speech.

    text: the sentence to speak. Keep this to a single sentence/short
          utterance -- SpeechT5 was fine-tuned on individual TORGO prompts,
          not long passages. Chunk longer text before calling (Person C's
          module handles stitching multiple calls back together).
    speaker_id: one of the TORGO speaker codes with a precomputed
          embedding (see embeddings/speaker_embeddings.pt) -- e.g. "MC04".
    speaker_embedding: OR pass a raw 512-dim tensor directly. This is
          where Person A's real speaker embedding plugs in once its
          format is confirmed (Sync Point 1) -- takes priority over
          speaker_id if both are given.

    Returns: 1D float32 numpy array, 16kHz mono.
    """
    if speaker_embedding is None and speaker_id is None:
        raise ValueError("Must provide either speaker_id or speaker_embedding")

    pipeline = _get_pipeline()
    device = pipeline["device"]

    if speaker_embedding is None:
        if speaker_id not in pipeline["speaker_embeddings"]:
            available = list(pipeline["speaker_embeddings"].keys())
            raise ValueError(f"Unknown speaker_id '{speaker_id}'. Available: {available}")
        speaker_embedding = pipeline["speaker_embeddings"][speaker_id]

    speaker_embedding = speaker_embedding.to(device)
    if speaker_embedding.dim() == 1:
        speaker_embedding = speaker_embedding.unsqueeze(0)

    inputs = pipeline["processor"](text=text, return_tensors="pt").to(device)

    with torch.no_grad():
        speech = pipeline["model"].generate_speech(
            inputs["input_ids"], speaker_embedding, vocoder=pipeline["vocoder"]
        )

    return speech.cpu().numpy().astype(np.float32)


if __name__ == "__main__":
    import sys
    import soundfile as sf

    if len(sys.argv) < 3:
        print("Usage: python src/inference/synthesize.py \"<text>\" <speaker_id>")
        sys.exit(1)

    text_arg = sys.argv[1]
    speaker_arg = sys.argv[2]

    audio = synthesize(text_arg, speaker_id=speaker_arg)
    out_path = "outputs/synthesize_cli_test.wav"
    sf.write(out_path, audio, samplerate=16000)
    print(f"Wrote {out_path} ({len(audio)/16000:.2f}s)")
