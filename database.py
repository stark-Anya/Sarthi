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
    # Keep old tables for backward compat (data safe)
    c.execute("""CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_num TEXT,
        subject TEXT,
        book_name TEXT NOT NULL,
        file_id TEXT,
        added_by INTEGER,
        created TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pyqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_type TEXT NOT NULL,
        title TEXT NOT NULL,
        file_id TEXT NOT NULL,
        file_name TEXT,
        added_by INTEGER,
        created TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS mix_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_name TEXT NOT NULL,
        file_id TEXT NOT NULL,
        file_name TEXT,
        added_by INTEGER,
        created TEXT DEFAULT (datetime('now'))
    )""")

    # ══════════════════════════════════════════════════════════════════════════
    #  MATERIALS TREE — ManyBot-style infinite nested folders
    #
    #  mat_nodes : folders/buttons (parent_id NULL = root of materials)
    #  mat_files : files inside a node (pdf / photo / text)
    # ══════════════════════════════════════════════════════════════════════════
    c.execute("""CREATE TABLE IF NOT EXISTS mat_nodes (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id  INTEGER,                         -- NULL = top-level (shown in materials home)
        name       TEXT NOT NULL,                   -- button label
        emoji      TEXT DEFAULT '📁',
        sort_order INTEGER DEFAULT 0,
        created    TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(parent_id) REFERENCES mat_nodes(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mat_files (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id    INTEGER NOT NULL,                -- which folder
        title      TEXT,                            -- display caption / title
        file_type  TEXT NOT NULL,                   -- 'pdf' | 'photo' | 'text'
        file_id    TEXT,                            -- telegram file_id (null for text)
        content    TEXT,                            -- text content (null for files)
        sort_order INTEGER DEFAULT 0,
        created    TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(node_id) REFERENCES mat_nodes(id)
    )""")

    # Seed default top-level nodes if empty (match existing sections)
    cnt = c.execute("SELECT COUNT(*) FROM mat_nodes WHERE parent_id IS NULL").fetchone()[0]
    if cnt == 0:
        defaults = [
            (None, "📚 Books",      "📚", 1),
            (None, "📐 Formulas",   "📐", 2),
            (None, "📋 PYQs",       "📋", 3),
            (None, "🔀 11 & 12 Mix","🔀", 4),
        ]
        for parent, name, emoji, order in defaults:
            c.execute("INSERT INTO mat_nodes (parent_id, name, emoji, sort_order) VALUES (?,?,?,?)",
                      (parent, name, emoji, order))

    conn.commit()
    conn.close()
    print("[DB] All tables ready.")


# ── Tree helpers ──────────────────────────────────────────────────────────────
def mat_get_children(parent_id):
    """Get child nodes of a folder. parent_id=None → top-level."""
    conn = get_conn()
    if parent_id is None:
        rows = conn.execute(
            "SELECT * FROM mat_nodes WHERE parent_id IS NULL ORDER BY sort_order, id"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM mat_nodes WHERE parent_id=? ORDER BY sort_order, id",
            (parent_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mat_get_node(node_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM mat_nodes WHERE id=?", (node_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def mat_get_files(node_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM mat_files WHERE node_id=? ORDER BY sort_order, id", (node_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mat_add_node(parent_id, name, emoji="📁"):
    conn = get_conn()
    c = conn.cursor()
    max_order = c.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM mat_nodes WHERE parent_id IS ?",
        (parent_id,)
    ).fetchone()[0]
    c.execute(
        "INSERT INTO mat_nodes (parent_id, name, emoji, sort_order) VALUES (?,?,?,?)",
        (parent_id, name, emoji, max_order + 1)
    )
    nid = c.lastrowid
    conn.commit(); conn.close()
    return nid


def mat_add_file(node_id, title, file_type, file_id=None, content=None):
    conn = get_conn()
    c = conn.cursor()
    max_order = c.execute(
        "SELECT COALESCE(MAX(sort_order),0) FROM mat_files WHERE node_id=?", (node_id,)
    ).fetchone()[0]
    c.execute(
        "INSERT INTO mat_files (node_id, title, file_type, file_id, content, sort_order) VALUES (?,?,?,?,?,?)",
        (node_id, title, file_type, file_id, content, max_order + 1)
    )
    fid = c.lastrowid
    conn.commit(); conn.close()
    return fid


def mat_delete_node(node_id):
    """Recursively delete node and all children + files."""
    conn = get_conn()
    _recursive_delete(conn, node_id)
    conn.commit(); conn.close()


def _recursive_delete(conn, node_id):
    children = conn.execute("SELECT id FROM mat_nodes WHERE parent_id=?", (node_id,)).fetchall()
    for ch in children:
        _recursive_delete(conn, ch["id"])
    conn.execute("DELETE FROM mat_files WHERE node_id=?", (node_id,))
    conn.execute("DELETE FROM mat_nodes WHERE id=?", (node_id,))


def mat_delete_file(file_id):
    conn = get_conn()
    conn.execute("DELETE FROM mat_files WHERE id=?", (file_id,))
    conn.commit(); conn.close()


def mat_rename_node(node_id, new_name, new_emoji=None):
    conn = get_conn()
    if new_emoji:
        conn.execute("UPDATE mat_nodes SET name=?, emoji=? WHERE id=?", (new_name, new_emoji, node_id))
    else:
        conn.execute("UPDATE mat_nodes SET name=? WHERE id=?", (new_name, node_id))
    conn.commit(); conn.close()


def mat_edit_file_title(file_id, new_title):
    conn = get_conn()
    conn.execute("UPDATE mat_files SET title=? WHERE id=?", (new_title, file_id))
    conn.commit(); conn.close()


def mat_get_breadcrumb(node_id):
    """Return list of (id, name) from root to node."""
    path = []
    conn = get_conn()
    current = node_id
    while current:
        row = conn.execute("SELECT id, name, parent_id FROM mat_nodes WHERE id=?", (current,)).fetchone()
        if not row:
            break
        path.insert(0, {"id": row["id"], "name": row["name"]})
        current = row["parent_id"]
    conn.close()
    return path


# ── Other helpers ─────────────────────────────────────────────────────────────
def upsert_user(tg_id: int, name: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (tg_id, name) VALUES (?, ?) ON CONFLICT(tg_id) DO UPDATE SET name=excluded.name",
        (tg_id, name)
    )
    conn.commit(); conn.close()


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
        conn.close(); return
    streak = row["streak"] or 0
    last_active = row["last_active"]
    if last_active == today_str:
        conn.close(); return
    if last_active:
        diff = (date.today() - date.fromisoformat(last_active)).days
        streak = streak + 1 if diff == 1 else 1
    else:
        streak = 1
    conn.execute("UPDATE users SET streak=?, last_active=? WHERE tg_id=?",
                 (streak, today_str, tg_id))
    conn.commit(); conn.close()


def get_sections():
    return mat_get_children(None)

def add_section(name):
    return mat_add_node(None, name)

def delete_section(section_id):
    return mat_delete_node(section_id)


def get_setting(key, default=None):
    return default
def set_setting(key, value):
    pass
def delete_setting(key):
    pass
