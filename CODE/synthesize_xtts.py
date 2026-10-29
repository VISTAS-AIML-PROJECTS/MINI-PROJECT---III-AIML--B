"""
src/inference/synthesize_xtts.py
THE core synthesis module for the real project -- XTTS-v2, chosen over
SpeechT5 after head-to-head testing showed XTTS actually captures real
speaker identity (correct gender, real timbre resemblance) out of the
box, while SpeechT5 fine-tuning never produced usable results despite
extensive debugging.

UPDATED: now defaults to the FINE-TUNED checkpoint (trained on real
recorded voice data) instead of the base XTTS-v2 model -- this captures
actual voice identity, not just generic zero-shot resemblance. Override
via env vars if you want to use the base model instead.

Simpler than the SpeechT5 pipeline: XTTS takes a reference audio clip
directly (no separate x-vector extraction step needed).

Usage:
    from src.inference.synthesize_xtts import synthesize, get_sample_rate
    audio = synthesize("Hello there.", speaker_wav_path="patient_ref.wav")
    sr = get_sample_rate()  # XTTS outputs at 24kHz, NOT 16kHz
"""

import os
import numpy as np
import torch

os.environ.setdefault("COQUI_TOS_AGREED", "1")  # skip interactive license prompt
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

# Fine-tuned checkpoint (trained on real recorded voice data) -- falls
# back to the base pretrained model if these files aren't found.
FINETUNED_DIR = os.environ.get(
    "XTTS_FINETUNED_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "finetuned_model"),
)
CHECKPOINT_PATH = os.path.join(FINETUNED_DIR, "best_model.pth")
CONFIG_PATH = os.path.join(FINETUNED_DIR, "config.json")
VOCAB_PATH = os.path.join(FINETUNED_DIR, "vocab.json")

_model = None


def _get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        if os.path.exists(CHECKPOINT_PATH):
            print(f"Loading FINE-TUNED XTTS model from {FINETUNED_DIR} (device={device})...")
            config = XttsConfig()
            config.load_json(CONFIG_PATH)
            model = Xtts.init_from_config(config)
            model.load_checkpoint(
                config, checkpoint_path=CHECKPOINT_PATH, vocab_path=VOCAB_PATH, use_deepspeed=False
            )
            model.to(device)
            model.eval()  # CRITICAL: without this, dropout/etc. stay active,
                          # causing unstable/garbled output -- this was missing
            _model = ("finetuned", model, config)
        else:
            print(f"Fine-tuned model not found at {FINETUNED_DIR} -- falling back to base XTTS-v2 (device={device})...")
            from TTS.api import TTS
            model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            _model = ("base", model, None)

    return _model


def get_sample_rate() -> int:
    """XTTS-v2 outputs at 24kHz -- important: this is different from the
    16kHz used throughout the earlier SpeechT5 pipeline. Any code stitching
    or saving XTTS output must use THIS rate, not a hardcoded 16000."""
    return 24000


def synthesize(text: str, speaker_wav_path: str, language: str = "en") -> np.ndarray:
    """
    Synthesize speech in the voice from speaker_wav_path, using the
    fine-tuned model if available (captures real voice identity), or
    falling back to base XTTS-v2 zero-shot cloning otherwise.

    text: sentence/text to speak.
    speaker_wav_path: path to a reference audio clip of the target voice.
    language: ISO language code, default "en".

    Returns: 1D float32 numpy array at get_sample_rate() (24kHz).
    """
    kind, model, config = _get_model()

    if kind == "finetuned":
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[speaker_wav_path])
        out = model.inference(
            text, language, gpt_cond_latent, speaker_embedding,
            temperature=config.temperature if config else 0.7,
        )
        wav = out["wav"]
    else:
        wav = model.tts(text=text, speaker_wav=speaker_wav_path, language=language)

    return np.array(wav, dtype=np.float32)

