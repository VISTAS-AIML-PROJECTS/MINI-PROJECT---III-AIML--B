"""
speech_cache.py
Caches synthesized speech by exact text (+voice/language/register/emotion),
so saying the same thing twice never re-runs the model -- and powers
autocomplete suggestions from your own speaking history.

SQLite for the index (stdlib, no new dependency), plain .wav files on disk
for the audio itself.
"""

import os
import sqlite3
import hashlib
import shutil

DB_PATH = "final_app/speech_cache.db"
CACHE_DIR = "final_app/cache_audio"
os.makedirs(CACHE_DIR, exist_ok=True)


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS speech_cache (
            key TEXT PRIMARY KEY,
            text TEXT,
            voice TEXT,
            language TEXT,
            register TEXT,
            emotion TEXT,
            wav_path TEXT,
            last_used TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn


def cache_key(text, voice, language, register, emotion):
    norm = text.strip().lower()
    raw = f"{norm}|{voice}|{language}|{register}|{emotion}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(text, voice, language, register, emotion):
    """Returns a wav file path if this exact utterance was synthesized
    before, else None. Touches last_used on hit."""
    key = cache_key(text, voice, language, register, emotion)
    conn = _conn()
    row = conn.execute("SELECT wav_path FROM speech_cache WHERE key=?", (key,)).fetchone()
    if row and os.path.exists(row[0]):
        conn.execute("UPDATE speech_cache SET last_used=CURRENT_TIMESTAMP WHERE key=?", (key,))
        conn.commit()
        conn.close()
        return row[0]
    conn.close()
    return None


def store(text, voice, language, register, emotion, src_wav_path):
    """Copies src_wav_path into the cache and indexes it under this
    utterance's key. Returns the cached path."""
    key = cache_key(text, voice, language, register, emotion)
    dest = os.path.join(CACHE_DIR, f"{key}.wav")
    shutil.copy2(src_wav_path, dest)

    conn = _conn()
    conn.execute(
        "INSERT OR REPLACE INTO speech_cache (key, text, voice, language, register, emotion, wav_path) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (key, text, voice, language, register or "", emotion or "neutral", dest),
    )
    conn.commit()
    conn.close()
    return dest


def suggest(prefix, voice, language, limit=3):
    """Returns up to `limit` previously-spoken texts (most recent first)
    that start with `prefix`, for this voice+language -- autocomplete."""
    if not prefix.strip():
        return []
    conn = _conn()
    rows = conn.execute(
        "SELECT DISTINCT text FROM speech_cache "
        "WHERE voice=? AND language=? AND text LIKE ? "
        "ORDER BY last_used DESC LIMIT ?",
        (voice, language, prefix + "%", limit),
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]
