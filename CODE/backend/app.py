from typing import Optional
from fastapi import FastAPI, Header, HTTPException, UploadFile, Form, File, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import config, phrasebank
from translate import translate

config.PHRASE_BANK.mkdir(parents=True, exist_ok=True)
config.CACHE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Echogenesis")
app.mount("/bank", StaticFiles(directory=config.PHRASE_BANK), name="bank")
app.mount("/cache", StaticFiles(directory=config.CACHE_DIR), name="cache")  # TODO: protect in production


def auth(x_api_key: str = Header(default="")):
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(401, "bad api key")


class SpeakReq(BaseModel):
    text: str
    voice: str = "male"
    language: str = "en"                 # language to speak in
    source_language: Optional[str] = None  # if set and different, text is translated first


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/voices", dependencies=[Depends(auth)])
def voices():
    return {"voices": list(config.VOICES), "synth_languages": sorted(config.XTTS_LANGS)}


@app.post("/speak", dependencies=[Depends(auth)])
def speak(r: SpeakReq):
    if r.voice not in config.VOICES:
        raise HTTPException(400, "unknown voice")
    text = r.text.strip()
    if not text:
        raise HTTPException(400, "empty text")
    if r.source_language and r.source_language != r.language:
        text = translate(text, r.source_language, r.language)

    hit = phrasebank.lookup(r.voice, r.language, text)
    if hit:
        return {"source": "recorded", "text": text, "audio_url": f"/bank/{r.voice}/{r.language}/{hit.name}"}

    if r.language not in config.XTTS_LANGS:
        # client should fall back to on-device TTS for this language
        return {"source": "unsupported", "text": text, "audio_url": None}

    import engine
    wav = engine.synthesize(r.voice, r.language, text)
    return {"source": "synthesized", "text": text, "audio_url": f"/cache/{wav.name}"}


@app.get("/phrases", dependencies=[Depends(auth)])
def phrases(voice: str, language: str = "en"):
    return {"phrases": [{**p, "audio_url": f"/bank/{voice}/{language}/{p['file']}"}
                        for p in phrasebank.list_phrases(voice, language)]}


@app.post("/phrases", dependencies=[Depends(auth)])
async def add_phrase(voice: str = Form(...), language: str = Form("en"),
                     text: str = Form(...), file: UploadFile = File(...)):
    if voice not in config.VOICES:
        raise HTTPException(400, "unknown voice")
    name = phrasebank.add(voice, language, text, await file.read())
    return {"saved": name}
