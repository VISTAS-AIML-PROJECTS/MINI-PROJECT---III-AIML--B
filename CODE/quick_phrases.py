"""
quick_phrases.py
For fixed sets of emergency (IDs 061-080) and common everyday (IDs
C01-C15) phrases, we keep the patient's REAL recorded audio and play
that back directly instead of running it through AI synthesis.

Voice-aware (male/female) AND language/register-aware:
  - English:      finetune_dataset/<voice>/wavs/
  - Tamil casual: finetune_dataset/<voice>/tamil_casual/wavs/
  - Tamil formal: finetune_dataset/<voice>/tamil_formal/wavs/

Usage:
    from quick_phrases import get_quick_phrase_audio, is_quick_phrase

    audio = get_quick_phrase_audio("Please, I need help right now.", voice="male", language="en")
    audio = get_quick_phrase_audio("தயவுசெஞ்சு, இப்போவே எனக்கு உதவி வேணும்.", voice="male", language="ta", register="casual")
"""

import os
import re
import librosa
import numpy as np

from english_common_prompts import common_en
from tamil_prompts import emergency_ta, common_ta

PROMPTS_FILE = "recording_prompts.md"
TARGET_SR = 24000  # match XTTS output rate so raw playback and AI output are interchangeable

EMERGENCY_ID_RANGE = (61, 80)

_cache = {}  # lazy-built {(voice, language, register): {normalized_text: wav_path}}


def _wavs_dir(voice: str, language: str, register: str | None) -> str:
    if language == "ta":
        return os.path.join("finetune_dataset", voice, f"tamil_{register}", "wavs")
    return os.path.join("finetune_dataset", voice, "wavs")


def _normalize(text: str) -> str:
    """Lowercase, strip whitespace/trailing punctuation for flexible matching."""
    text = text.strip().lower()
    text = re.sub(r"[.!?]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _english_emergency_texts():
    """{prompt_id: text} for IDs 061-080, parsed from recording_prompts.md."""
    texts = {}
    if not os.path.exists(PROMPTS_FILE):
        return texts
    with open(PROMPTS_FILE) as f:
        for line in f:
            m = re.match(r"^(\d{3})\.\s+(.+)$", line.strip())
            if not m:
                continue
            pid, text = m.groups()
            num = int(pid)
            if EMERGENCY_ID_RANGE[0] <= num <= EMERGENCY_ID_RANGE[1]:
                texts[pid] = text
    return texts


def _prompt_texts(language: str, register: str | None):
    """Returns {prompt_id: text} covering both emergency + common IDs
    for the given language/register."""
    if language == "ta":
        texts = {pid: entry[register] for pid, entry in emergency_ta.items()}
        texts.update({pid: entry[register] for pid, entry in common_ta.items()})
        return texts
    # English
    texts = dict(_english_emergency_texts())
    texts.update(common_en)
    return texts


def _build_lookup(voice: str, language: str, register: str | None):
    key = (voice, language, register)
    if key in _cache:
        return _cache[key]

    lookup = {}
    wavs_dir = _wavs_dir(voice, language, register)
    for prompt_id, text in _prompt_texts(language, register).items():
        wav_path = os.path.join(wavs_dir, f"prompt_{prompt_id}.wav")
        if os.path.exists(wav_path):
            lookup[_normalize(text)] = wav_path

    _cache[key] = lookup
    return lookup


def is_quick_phrase(text: str, voice: str = "male", language: str = "en", register: str | None = None) -> bool:
    lookup = _build_lookup(voice, language, register)
    return _normalize(text) in lookup


def get_quick_phrase_audio(text: str, voice: str = "male", language: str = "en", register: str | None = None):
    """
    Returns the REAL recorded audio for this phrase, resampled to match
    the AI pipeline's output rate (24kHz). Returns None if no match --
    caller should fall back to synthesize().
    """
    lookup = _build_lookup(voice, language, register)
    wav_path = lookup.get(_normalize(text))
    if wav_path is None:
        return None

    audio, sr = librosa.load(wav_path, sr=None, mono=True)
    if sr != TARGET_SR:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)

    return audio.astype(np.float32)


def is_emergency_phrase(text: str, voice: str = "male", language: str = "en", register: str | None = None) -> bool:
    """True if this text matches a known phrase AND that phrase's id is
    in the emergency range (061-080), as opposed to common (C01-C15)."""
    lookup = _build_lookup(voice, language, register)
    key = _normalize(text)
    if key not in lookup:
        return False
    wav_path = lookup[key]
    prompt_id = os.path.basename(wav_path).replace("prompt_", "").replace(".wav", "")
    return prompt_id.isdigit() and EMERGENCY_ID_RANGE[0] <= int(prompt_id) <= EMERGENCY_ID_RANGE[1]


def list_quick_phrases(voice: str = "male", language: str = "en", register: str | None = None):
    lookup = _build_lookup(voice, language, register)
    return sorted(lookup.keys())


def list_quick_phrases_display(voice: str = "male", language: str = "en", register: str | None = None):
    """
    Returns [(prompt_id, text, english_text)] for phrases that have a
    real recording -- english_text is the same as text when language is
    "en", otherwise the English equivalent for that prompt id (useful
    for showing bilingual button labels in the UI). IDs starting with a
    digit are emergency (061-080), IDs starting with "C" are common
    (C01-C15). Sorted so emergency phrases come first, then common,
    each in order.
    """
    results = []
    wavs_dir = _wavs_dir(voice, language, register)
    texts = _prompt_texts(language, register)
    english_texts = texts if language == "en" else _prompt_texts("en", None)

    for prompt_id, text in texts.items():
        wav_path = os.path.join(wavs_dir, f"prompt_{prompt_id}.wav")
        if os.path.exists(wav_path):
            english_text = english_texts.get(prompt_id, text)
            results.append((prompt_id, text, english_text))

    def sort_key(item):
        pid = item[0]
        return (0, pid) if pid[0].isdigit() else (1, pid)

    return sorted(results, key=sort_key)


if __name__ == "__main__":
    for v in ("male", "female"):
        print(f"[{v}] English: {len(list_quick_phrases(v, 'en'))} phrases")
    for reg in ("casual", "formal"):
        print(f"[male] Tamil {reg}: {len(list_quick_phrases('male', 'ta', reg))} phrases")
