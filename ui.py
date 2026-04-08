from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup

E = {
    "today":    "📅",
    "memories": "🧠",
    "formulas": "📐",
    "thoughts": "💭",
    "motivation": "🔥",
    "admin":    "🛡️",
    "back":     "◀️",
    "cancel":   "❌",
    "done":     "✅",
    "delete":   "🗑️",
    "edit":     "✏️",
    "add":      "➕",
    "timer":    "⏱️",
    "task":     "📝",
    "lecture":  "🎥",
    "score":    "📊",
    "doubt":    "❓",
    "revision": "🔄",
    "prev":     "⬅️",
    "next":     "➡️",
    "silly":    "🤪",
    "error":    "❗",
    "important":"⭐",
    "log":      "📒",
    "formula":  "🔢",
    "broadcast":"📢",
    "stats":    "📈",
    "users":    "👥",
    "ban":      "🚫",
    "unban":    "✅",
    "search":   "🔍",
    "skip":     "⏭️",
    "snooze":   "😴",
    "watch":    "👁️",
    "link":     "🔗",
    "phy":      "⚛️",
    "chem":     "🧪",
    "math":     "📏",
    "bio":      "🌿",
    "other":    "📌",
}


def home_kb():
    return Markup([
        [Btn(f"{E['today']} Today",      callback_data="today_home"),
         Btn(f"{E['memories']} Memories", callback_data="mem_home")],
        [Btn("📚 Materials",               callback_data="materials_home"),
         Btn(f"{E['thoughts']} Thoughts",  callback_data="thought_home")],
        [Btn(f"{E['motivation']} Motivation", callback_data="motiv_home"),
         Btn("📊 Stats",                      callback_data="stats_home")],
        [Btn(f"{E['admin']} Admin",           callback_data="admin_home")],
    ])


def today_home_kb():
    return Markup([
        [Btn(f"{E['add']} Add Task",       callback_data="task_add"),
         Btn(f"{E['task']} My Tasks",      callback_data="task_list")],
        [Btn(f"{E['add']} Add Lecture",    callback_data="lec_add"),
         Btn(f"{E['lecture']} Lectures",   callback_data="lec_list")],
        [Btn(f"{E['timer']} Focus Timer",  callback_data="timer_home"),
         Btn(f"{E['score']} Test Scores",  callback_data="score_home")],
        [Btn(f"{E['doubt']} Doubts",       callback_data="doubt_home"),
         Btn(f"{E['revision']} Revisions", callback_data="revision_home")],
        [Btn(f"{E['back']} Back",          callback_data="home")],
    ])


def mem_home_kb():
    return Markup([
        [Btn(f"{E['silly']} Silly",         callback_data="mem_silly"),
         Btn(f"{E['error']} Error",         callback_data="mem_error"),
         Btn(f"{E['important']} Important", callback_data="mem_important")],
        [Btn(f"{E['log']} Daily Log",       callback_data="daily_log_home")],
        [Btn(f"{E['back']} Back",           callback_data="home")],
    ])


def cancel_btn(callback: str):
    return Markup([[Btn(f"{E['cancel']} Cancel", callback_data=callback)]])


def back_btn(callback: str):
    return Markup([[Btn(f"{E['back']} Back", callback_data=callback)]])


def confirm_delete_kb(yes_cb: str, no_cb: str):
    return Markup([
        [Btn("🗑️ Yes, delete it", callback_data=yes_cb)],
        [Btn("↩️ No, keep it",    callback_data=no_cb)],
    ])


def subject_kb(prefix: str):
    return Markup([
        [Btn(f"{E['phy']} PHY",   callback_data=f"{prefix}_PHY"),
         Btn(f"{E['chem']} CHEM", callback_data=f"{prefix}_CHEM")],
        [Btn(f"{E['math']} MATH", callback_data=f"{prefix}_MATH"),
         Btn(f"{E['bio']} BIO",   callback_data=f"{prefix}_BIO")],
        [Btn(f"{E['other']} OTHER", callback_data=f"{prefix}_OTHER")],
    ])


def timer_kb():
    return Markup([
        [Btn("25 min", callback_data="timer_25"),
         Btn("50 min", callback_data="timer_50")],
        [Btn("15 min", callback_data="timer_15"),
         Btn("✏️ Custom", callback_data="timer_custom")],
        [Btn(f"{E['back']} Back", callback_data="today_home")],
    ])


def nav_kb(section: str, idx: int, total: int, extra_rows=None):
    nav_row = [
        Btn(f"{E['prev']} Prev", callback_data=f"{section}_nav_{idx - 1}") if idx > 0 else Btn("·", callback_data="noop"),
        Btn(f"{idx + 1}/{total}", callback_data="noop"),
        Btn(f"Next {E['next']}", callback_data=f"{section}_nav_{idx + 1}") if idx < total - 1 else Btn("·", callback_data="noop"),
    ]
    rows = [nav_row]
    if extra_rows:
        rows.extend(extra_rows)
    return Markup(rows)


def skip_btn(callback: str):
    return Markup([[Btn(f"{E['skip']} Skip", callback_data=callback)]])
