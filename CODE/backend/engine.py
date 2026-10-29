import hashlib, re, threading
from pathlib import Path
import numpy as np
import soundfile as sf
from config import VOICES, CACHE_DIR, N_REFERENCE_CLIPS, MAX_CHUNK_CHARS

SR = 24000
_lock = threading.Lock()
_models = {}     # key: checkpoint dir string or "base" -> Xtts model
_latents = {}    # key: voice -> (gpt_cond_latent, speaker_embedding)


def _ft_ready(d):
    return d and all((Path(d) / f).exists() for f in ("best_model.pth", "config.json", "vocab.json"))


def _load_model(voice):
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    ckpt = VOICES[voice]["checkpoint_dir"]
    if _ft_ready(ckpt):
        key, cfg_dir, ckpt_file, vocab = str(ckpt), Path(ckpt), Path(ckpt) / "best_model.pth", Path(ckpt) / "vocab.json"
    else:
        key = "base"
        if key not in _models:
            from TTS.utils.manage import ModelManager
            cfg_dir, _, _ = ModelManager().download_model("tts_models/multilingual/multi-dataset/xtts_v2")
            cfg_dir = Path(cfg_dir)
        else:
            cfg_dir = None
        ckpt_file = vocab = None
    if key in _models:
        return key, _models[key]
    cfg = XttsConfig(); cfg.load_json(str(cfg_dir / "config.json"))
    m = Xtts.init_from_config(cfg)
    if ckpt_file:
        m.load_checkpoint(cfg, checkpoint_path=str(ckpt_file), vocab_path=str(vocab), use_deepspeed=False)
    else:
        m.load_checkpoint(cfg, checkpoint_dir=str(cfg_dir), use_deepspeed=False)
    try:
        import torch
        if torch.cuda.is_available():
            m.cuda()
    except Exception:
        pass
    _models[key] = m
    print(f"[engine] loaded {'fine-tuned ' + key if key != 'base' else 'BASE XTTS-v2'} for voice '{voice}'")
    return key, m


def _clips(voice):
    d = Path(VOICES[voice]["reference_dir"])
    files = sorted(d.glob("*.wav"))[:N_REFERENCE_CLIPS]
    if not files:
        raise RuntimeError(f"No reference wavs in {d}")
    return [str(f) for f in files]


def _split(text, limit=MAX_CHUNK_CHARS):
    parts = re.split(r"(?<=[.!?。！？])\s+", text.strip())
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= limit:
            cur = f"{cur} {p}".strip()
        else:
            if cur: out.append(cur)
            while len(p) > limit:
                cut = p.rfind(" ", 0, limit); cut = cut if cut > 0 else limit
                out.append(p[:cut]); p = p[cut:].strip()
            cur = p
    if cur: out.append(cur)
    return out


def synthesize(voice, lang, text) -> Path:
    """Return path to a wav for `text`. Results are cached, so repeats are instant."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = CACHE_DIR / (hashlib.sha1(f"{voice}|{lang}|{text}".encode()).hexdigest() + ".wav")
    if out.exists():
        return out
    with _lock:
        key, model = _load_model(voice)
        if voice not in _latents:
            _latents[voice] = model.get_conditioning_latents(audio_path=_clips(voice))
        gpt, spk = _latents[voice]
        pieces, gap = [], np.zeros(int(SR * 0.15), dtype=np.float32)
        for chunk in _split(text):
            r = model.inference(chunk, lang, gpt, spk, temperature=0.7)
            pieces += [np.asarray(r["wav"], dtype=np.float32), gap]
        sf.write(out, np.concatenate(pieces[:-1]), SR)
    return out
