"""
load_model.py
Step 4 of the blueprint's build order.

Purpose: load pretrained SpeechT5 (processor + TTS model) and the matching
HiFi-GAN vocoder. Later, load_tts_model() will also accept a path to your
own fine-tuned checkpoint (Milestone 5+), but for now (Milestone 2) it just
loads the stock pretrained weights so you can sanity-check the pipeline.
"""

from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
import torch


def load_tts_model(checkpoint_path: str | None = None):
    """
    Load the SpeechT5 processor + TTS model.

    checkpoint_path: if None, loads the stock pretrained Microsoft checkpoint.
    If given, loads your fine-tuned weights instead (used from Milestone 5 on).
    """
    processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")

    if checkpoint_path is None:
        model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
    else:
        model = SpeechT5ForTextToSpeech.from_pretrained(checkpoint_path)

    model.eval()
    return processor, model


def load_vocoder(checkpoint_path: str | None = None):
    """
    Load the HiFi-GAN vocoder that matches SpeechT5's mel output.
    microsoft/speecht5_hifigan is pretrained specifically to match
    SpeechT5's mel config — no manual param alignment needed (Section 7).
    """
    if checkpoint_path is None:
        vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
    else:
        vocoder = SpeechT5HifiGan.from_pretrained(checkpoint_path)

    vocoder.eval()
    return vocoder


def get_device():
    """
    M1/M2/M3 Macs have no CUDA GPU — they use Apple's Metal (MPS) backend
    instead. This picks MPS if available, otherwise falls back to CPU.
    Some ops in SpeechT5 aren't yet supported on MPS; if you hit an error
    mentioning 'not implemented for MPS', set device back to 'cpu' — it's
    slower but always works, and inference (this script) is fast enough
    on CPU alone for single sentences.
    """
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
