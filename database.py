import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'resume_intelligence.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                filename TEXT,
                job_title TEXT,
                match_score REAL,
                result_json TEXT NOT NULL
            )
        ''')
        conn.commit()


def save_analysis(filename, job_title, match_score, result):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            'INSERT INTO analyses (created_at, filename, job_title, match_score, result_json) VALUES (?, ?, ?, ?, ?)',
            (datetime.utcnow().isoformat(), filename, job_title, match_score, json.dumps(result, ensure_ascii=False))
        )
        conn.commit()
        return cur.lastrowid
