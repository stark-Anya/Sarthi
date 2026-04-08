import sqlite3
from datetime import date, datetime, timedelta
import pytz
from config import DB_PATH, TIMEZONE

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE NOT NULL,
        name TEXT,
        streak INTEGER DEFAULT 0,
        last_active TEXT,
        is_banned INTEGER DEFAULT 0,
        joined TEXT DEFAULT (date('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        subject TEXT,
        done INTEGER DEFAULT 0,
        date TEXT DEFAULT (date('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lectures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        link TEXT,
        subject TEXT,
        alert_time TEXT,
        message TEXT,
        repeat_daily INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mem_type TEXT NOT NULL,
        title TEXT,
        content TEXT,
        file_id TEXT,
        file_type TEXT,
        answer TEXT,
        ans_file TEXT,
        ans_ftype TEXT,
        keypoints TEXT,
        created TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS daily_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        content TEXT,
        file_id TEXT,
        file_type TEXT,
        created TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, date),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS thoughts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT,
        file_id TEXT,
        file_type TEXT,
        created TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS formulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_num TEXT NOT NULL,
        chapter TEXT NOT NULL,
        subject TEXT,
        file_id TEXT,
        file_type TEXT,
        content TEXT,
        added_by INTEGER,
        created TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS motivation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT,
        file_id TEXT,
        file_type TEXT,
        created TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS study_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT,
        minutes INTEGER,
        date TEXT DEFAULT (date('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS test_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        test_name TEXT,
        phy REAL,
        chem REAL,
        math REAL,
        total REAL,
        date TEXT DEFAULT (date('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS revision_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        lecture_id INTEGER,
        topic TEXT,
        due_date TEXT,
        done INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS doubts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT,
        text TEXT,
        resolved INTEGER DEFAULT 0,
        created TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_num TEXT NOT NULL,
        subject TEXT NOT NULL,
        book_name TEXT NOT NULL,
        file_id TEXT,
        added_by INTEGER,
        created TEXT DEFAULT (datetime('now'))
    )""")

    conn.commit()
    conn.close()
    print("[DB] All tables ready.")


def upsert_user(tg_id: int, name: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (tg_id, name) VALUES (?, ?) ON CONFLICT(tg_id) DO UPDATE SET name=excluded.name",
        (tg_id, name)
    )
    conn.commit()
    conn.close()


def get_user(tg_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def is_banned(tg_id: int) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT is_banned FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    conn.close()
    return bool(row and row["is_banned"])


def get_all_users():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM users WHERE is_banned=0").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_streak(tg_id: int):
    today_str = date.today().isoformat()
    conn = get_conn()
    row = conn.execute("SELECT streak, last_active FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    if not row:
        conn.close()
        return
    streak = row["streak"] or 0
    last_active = row["last_active"]
    if last_active == today_str:
        conn.close()
        return
    if last_active:
        last_dt = date.fromisoformat(last_active)
        diff = (date.today() - last_dt).days
        if diff == 1:
            streak += 1
        elif diff > 1:
            streak = 1
    else:
        streak = 1
    conn.execute(
        "UPDATE users SET streak=?, last_active=? WHERE tg_id=?",
        (streak, today_str, tg_id)
    )
    conn.commit()
    conn.close()
