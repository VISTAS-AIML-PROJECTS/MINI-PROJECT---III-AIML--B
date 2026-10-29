"""
src/inference/synthesize_xtts.py
Core synthesis module -- XTTS-v2, now voice-aware (male/female).

Male voice: uses the fine-tuned checkpoint (finetuned_model/male/), since
it's trained on real recorded voice data -- captures actual identity.

Female voice: uses base pretrained XTTS-v2 with zero-shot cloning from
her raw reference recordings, until a dedicated fine-tuned checkpoint
exists for her (finetuned_model/female/) -- at which point this will
pick that up automatically, same as male.

Usage:
    from src.inference.synthesize_xtts import synthesize, get_sample_rate
    audio = synthesize("Hello there.", speaker_wav_path="patient_ref.wav", voice="male")
    sr = get_sample_rate()  # XTTS outputs at 24kHz, NOT 16kHz
"""

import os
import numpy as np
import torch

os.environ.setdefault("COQUI_TOS_AGREED", "1")  # skip interactive license prompt
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_models = {}  # {voice: (kind, model, config)} -- one loaded model per voice
_base_model = None  # shared base XTTS-v2, lazy-loaded once, reused across voices that need it


def _finetuned_paths(voice: str):
    d = os.path.join(PROJECT_ROOT, "finetuned_model", voice)
    return (
        os.path.join(d, "best_model.pth"),
        os.path.join(d, "config.json"),
        os.path.join(d, "vocab.json"),
    )


def _get_base_model(device):
    global _base_model
    if _base_model is None:
        print("Loading BASE XTTS-v2 (zero-shot cloning)...")
        from TTS.api import TTS
        _base_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    return _base_model


def _get_model(voice: str = "male"):
    if voice in _models:
        return _models[voice]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint_path, config_path, vocab_path = _finetuned_paths(voice)

    if os.path.exists(checkpoint_path):
        print(f"Loading FINE-TUNED XTTS model for '{voice}' (device={device})...")
        config = XttsConfig()
        config.load_json(config_path)
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_path=checkpoint_path, vocab_path=vocab_path, use_deepspeed=False)
        model.to(device)
        model.eval()  # CRITICAL: without this, dropout/etc. stay active, causing unstable/garbled output
        _models[voice] = ("finetuned", model, config)
    else:
        print(f"No fine-tuned checkpoint for '{voice}' yet -- using base XTTS-v2 zero-shot cloning (device={device})...")
        model = _get_base_model(device)
        _models[voice] = ("base", model, None)

    return _models[voice]


def get_sample_rate() -> int:
    """XTTS-v2 outputs at 24kHz for both fine-tuned and base models."""
    return 24000


def synthesize(text: str, speaker_wav_path, voice: str = "male", language: str = "en") -> np.ndarray:
    """
    Synthesize speech in the given voice ("male" or "female"), using that
    voice's fine-tuned checkpoint if available, or base XTTS-v2 zero-shot
    cloning from speaker_wav_path otherwise.

    text: sentence/text to speak.
    speaker_wav_path: path (str) OR list of paths to reference audio
        clip(s) of the target voice.
    voice: "male" or "female" -- selects which model/checkpoint to use.
    language: ISO language code, default "en".

    Returns: 1D float32 numpy array at get_sample_rate() (24kHz).
    """
    kind, model, config = _get_model(voice)

    paths = [speaker_wav_path] if isinstance(speaker_wav_path, str) else list(speaker_wav_path)

    if kind == "finetuned":
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=paths)
        out = model.inference(
            text, language, gpt_cond_latent, speaker_embedding,
            temperature=config.temperature if config else 0.7,
        )
        wav = out["wav"]
    else:
        wav = model.tts(text=text, speaker_wav=paths[0], language=language)

    return np.array(wav, dtype=np.float32)
