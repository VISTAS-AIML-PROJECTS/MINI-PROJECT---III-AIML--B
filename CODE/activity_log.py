"""
activity_log.py
Logs every utterance spoken through the app -- powers the caregiver
dashboard's activity feed and emergency alerts. Also stores
caregiver-added custom phrases (text only; synthesized via AI like any
free-text, since no real recording exists for them).
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = "final_app/speech_cache.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            voice TEXT,
            language TEXT,
            emotion TEXT,
            is_emergency INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_phrases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            voice TEXT,
            language TEXT,
            added_by TEXT DEFAULT 'caregiver',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn


def log_event(text, voice, language, emotion, is_emergency):
    conn = _conn()
    conn.execute(
        "INSERT INTO activity_log (text, voice, language, emotion, is_emergency) VALUES (?, ?, ?, ?, ?)",
        (text, voice, language, emotion, int(is_emergency)),
    )
    conn.commit()
    conn.close()


def recent(limit=25):
    conn = _conn()
    rows = conn.execute(
        "SELECT text, voice, language, emotion, is_emergency, timestamp "
        "FROM activity_log ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {"text": r[0], "voice": r[1], "language": r[2], "emotion": r[3],
         "is_emergency": bool(r[4]), "timestamp": r[5]}
        for r in rows
    ]


def last_emergency():
    conn = _conn()
    row = conn.execute(
        "SELECT text, timestamp FROM activity_log WHERE is_emergency=1 "
        "ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    ts = datetime.fromisoformat(row[1])
    minutes_ago = (datetime.utcnow() - ts).total_seconds() / 60
    return {"text": row[0], "timestamp": row[1], "minutes_ago": round(minutes_ago, 1)}


def stats():
    conn = _conn()
    today_start = datetime.utcnow().strftime("%Y-%m-%d 00:00:00")
    week_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
    today_count = conn.execute(
        "SELECT COUNT(*) FROM activity_log WHERE timestamp >= ?", (today_start,)
    ).fetchone()[0]
    week_count = conn.execute(
        "SELECT COUNT(*) FROM activity_log WHERE timestamp >= ?", (week_start,)
    ).fetchone()[0]
    conn.close()
    return {"today": today_count, "week": week_count}


def add_custom_phrase(text, voice, language):
    conn = _conn()
    conn.execute(
        "INSERT INTO custom_phrases (text, voice, language) VALUES (?, ?, ?)",
        (text, voice, language),
    )
    conn.commit()
    conn.close()


def list_custom_phrases(voice, language):
    conn = _conn()
    rows = conn.execute(
        "SELECT id, text FROM custom_phrases WHERE voice=? AND language=? ORDER BY timestamp DESC",
        (voice, language),
    ).fetchall()
    conn.close()
    return [{"id": f"custom_{r[0]}", "text": r[1]} for r in rows]


def delete_custom_phrase(phrase_id):
    conn = _conn()
    conn.execute("DELETE FROM custom_phrases WHERE id=?", (phrase_id,))
    conn.commit()
    conn.close()
