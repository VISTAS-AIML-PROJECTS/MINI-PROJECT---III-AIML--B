import json, re, unicodedata
from pathlib import Path
from config import PHRASE_BANK


def normalize(text: str) -> str:
    """Exact-match key: case-folded, punctuation removed, spaces collapsed.
    Keeps letters, combining marks and digits so Indic scripts survive."""
    t = unicodedata.normalize("NFKC", text).casefold()
    t = "".join(c if (unicodedata.category(c)[0] in "LMN" or c.isspace()) else " " for c in t)
    return re.sub(r"\s+", " ", t).strip()


def _dir(voice, lang) -> Path:
    return PHRASE_BANK / voice / lang


def _load(voice, lang) -> dict:
    m = _dir(voice, lang) / "manifest.json"
    return json.loads(m.read_text(encoding="utf-8")) if m.exists() else {}


def lookup(voice, lang, text):
    """Return the recorded wav Path for an exact (normalized) match, else None."""
    entry = _load(voice, lang).get(normalize(text))
    if not entry:
        return None
    p = _dir(voice, lang) / entry["file"]
    return p if p.exists() else None


def add(voice, lang, text, wav_bytes: bytes):
    d = _dir(voice, lang)
    d.mkdir(parents=True, exist_ok=True)
    manifest = _load(voice, lang)
    key = normalize(text)
    fname = manifest[key]["file"] if key in manifest else f"{len(manifest) + 1:04d}.wav"
    (d / fname).write_bytes(wav_bytes)
    manifest[key] = {"file": fname, "text": text.strip()}
    (d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return fname


def list_phrases(voice, lang):
    return [{"text": v["text"], "file": v["file"]} for v in _load(voice, lang).values()]
