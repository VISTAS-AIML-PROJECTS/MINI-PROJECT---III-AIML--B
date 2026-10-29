"""
final_app/app.py
EchoGenesis: emergency + common quick-phrase buttons (real recordings),
free-text AI speech with emotion-reference selection, speech caching, and
typing suggestions from past speech -- Male/Female voices, English / Tamil
(casual + formal).

Run from the project root:
    python -m uvicorn final_app.app:app --host 0.0.0.0 --port 8002
"""

import os
import sys
import uuid
import soundfile as sf
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrate_pipeline_v2 import chunk_text, synthesize_with_quick_phrase_check, prepare_reference_audio
from src.inference.synthesize_xtts import get_sample_rate
from quick_phrases import list_quick_phrases_display, is_emergency_phrase
import speech_cache
import voice_banking
import activity_log

app = FastAPI(title="EchoGenesis")

REFERENCE_CLIPS = {
    "male": [
        "finetune_dataset/male/wavs/prompt_029.wav",
        "finetune_dataset/male/wavs/prompt_047.wav",
    ],
    "female": [
        "finetune_dataset/female/wavs/prompt_029.wav",
        "finetune_dataset/female/wavs/prompt_047.wav",
    ],
}

# Emotion -> real recorded reference clip (male only, English only, for now).
# Swaps XTTS's conditioning clip so output leans toward that clip's vocal
# character -- an approximation of emotion, not literal per-word acting.
EMOTION_CLIPS = {
    "male": {
        "urgent": "voice_recordings_v2_wav/angry.wav",
        "happy": "voice_recordings_v2_wav/excitement.wav",
        "calm": "voice_recordings_v2_wav/calm.wav",
        "sad": "voice_recordings_v2_wav/sadness.wav",
        "surprised": "voice_recordings_v2_wav/surprised.wav",
        "playful": "voice_recordings_v2_wav/sarcastic.wav",
        "whisper": "voice_recordings_v2_wav/whisper.wav",
    }
}

OUTPUT_DIR = "final_app/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="final_app/static"), name="static")

_reference_path_cache = {}


def _voice_available(voice: str) -> bool:
    return any(os.path.exists(p) for p in REFERENCE_CLIPS.get(voice, []))


def _get_reference_path(voice: str, emotion: str = "neutral"):
    clip = EMOTION_CLIPS.get(voice, {}).get(emotion)
    if clip and os.path.exists(clip):
        return clip  # single emotional clip, used as-is each time (not cached/prepared)

    cache_key = voice
    if cache_key not in _reference_path_cache:
        # Prefer the voice bank's similarity-to-baseline ranked clips --
        # this is the degradation-robust identity selection. Falls back
        # to the fixed default clips if no bank exists for this voice yet.
        clips = voice_banking.weighted_references(voice, n=2)
        if not clips:
            clips = [p for p in REFERENCE_CLIPS[voice] if os.path.exists(p)]
        if not clips:
            raise ValueError(f"No reference recordings found for voice '{voice}'")
        _reference_path_cache[cache_key] = prepare_reference_audio(clips)
    return _reference_path_cache[cache_key]


@app.get("/", response_class=HTMLResponse)
def index():
    with open("final_app/static/index.html") as f:
        return f.read()


@app.get("/voices")
def get_voices():
    return {"male": _voice_available("male"), "female": _voice_available("female")}


@app.get("/voice_bank_report")
def get_voice_bank_report(voice: str = "male"):
    """Identity drift report -- how closely each recording session
    matches the original baseline voice."""
    return {"sessions": voice_banking.drift_report(voice)}


@app.post("/voice_bank/checkin")
async def voice_bank_checkin(voice: str = Form("male"), audio: UploadFile = File(...)):
    """Accepts a short in-browser recording, converts it, and adds it to
    the voice bank as a new dated session -- no terminal needed."""
    import tempfile, shutil, subprocess
    from datetime import date

    tmp_dir = tempfile.mkdtemp()
    try:
        raw_path = os.path.join(tmp_dir, "checkin_raw")
        with open(raw_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        wav_path = os.path.join(tmp_dir, "checkin.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", raw_path,
             "-ar", "16000", "-ac", "1", wav_path],
            check=True,
        )

        label = f"checkin_{date.today()}"
        voice_banking.add_session(voice, tmp_dir, label)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    report = voice_banking.drift_report(voice)
    latest = report[-1] if report else None
    return {"status": "ok", "latest": latest}


@app.get("/quick_phrases")
def get_quick_phrases(voice: str = "male", language: str = "en", register: str | None = None):
    phrases = list_quick_phrases_display(voice, language, register)
    result = [{"id": pid, "text": text, "english": eng} for pid, text, eng in phrases]
    for cp in activity_log.list_custom_phrases(voice, language):
        result.append({"id": cp["id"], "text": cp["text"], "english": cp["text"]})
    return {"phrases": result}


@app.get("/quick_phrase_audio/{phrase_id}")
def get_quick_phrase_audio_by_id(phrase_id: str, voice: str = "male", language: str = "en", register: str | None = None):
    """Direct GET-cacheable audio for a real-recording phrase (emergency
    or common only, not AI-synthesized custom phrases) -- this is what
    the service worker pre-caches so these play with zero network."""
    import tempfile
    from quick_phrases import get_quick_phrase_audio

    phrases = {pid: text for pid, text, _ in list_quick_phrases_display(voice, language, register)}
    text = phrases.get(phrase_id)
    if text is None:
        return {"error": "Unknown phrase id"}

    audio = get_quick_phrase_audio(text, voice=voice, language=language, register=register)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, samplerate=get_sample_rate())
    return FileResponse(tmp.name, media_type="audio/wav", filename=f"{phrase_id}.wav")


@app.get("/caregiver", response_class=HTMLResponse)
def caregiver_page():
    with open("final_app/static/caregiver.html") as f:
        return f.read()


@app.get("/activity/recent")
def get_recent_activity(limit: int = 25):
    return {
        "recent": activity_log.recent(limit),
        "last_emergency": activity_log.last_emergency(),
        "stats": activity_log.stats(),
    }


@app.post("/activity/add_phrase")
async def add_custom_phrase(text: str = Form(...), voice: str = Form("male"), language: str = Form("en")):
    activity_log.add_custom_phrase(text, voice, language)
    return {"status": "ok"}


@app.post("/activity/delete_phrase")
async def delete_custom_phrase(phrase_id: int = Form(...)):
    activity_log.delete_custom_phrase(phrase_id)
    return {"status": "ok"}


@app.get("/suggest")
def get_suggestions(prefix: str, voice: str = "male", language: str = "en"):
    return {"suggestions": speech_cache.suggest(prefix, voice, language)}


@app.post("/speak")
async def speak(
    text: str = Form(...),
    voice: str = Form("male"),
    language: str = Form("en"),
    register: str | None = Form(None),
    emotion: str = Form("neutral"),
):
    activity_log.log_event(
        text, voice, language, emotion,
        is_emergency=is_emergency_phrase(text, voice, language, register),
    )

    cached_path = speech_cache.get_cached(text, voice, language, register, emotion)
    if cached_path:
        return FileResponse(cached_path, media_type="audio/wav", filename="speech_cached.wav")

    if language == "en" and not _voice_available(voice):
        return {"error": f"Voice '{voice}' is not available yet."}

    reference_path = _get_reference_path(voice, emotion) if language == "en" else None

    chunks = chunk_text(text)
    sample_rate = get_sample_rate()

    chunk_audio = []
    for chunk in chunks:
        audio = synthesize_with_quick_phrase_check(
            chunk, reference_path, voice=voice, language=language, register=register
        )
        if audio is None:
            return {"error": "AI speech isn't trained yet for this language. Try an exact quick phrase instead."}
        chunk_audio.append(audio)

    from stitch_audio import stitch
    final_audio = stitch(chunk_audio, sample_rate=sample_rate)

    out_filename = f"speech_{uuid.uuid4().hex}.wav"
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    sf.write(out_path, final_audio, samplerate=sample_rate)

    speech_cache.store(text, voice, language, register, emotion, out_path)

    return FileResponse(out_path, media_type="audio/wav", filename=out_filename)


@app.post("/activity/log")
async def log_press(
    text: str = Form(...),
    voice: str = Form("male"),
    language: str = Form("en"),
    register: str | None = Form(None),
):
    """Logs a button press that played straight from a real recording
    (not via /speak), so the caregiver feed and emergency alerts see it."""
    activity_log.log_event(
        text, voice, language, "neutral",
        is_emergency=is_emergency_phrase(text, voice, language, register),
    )
    return {"status": "ok"}
