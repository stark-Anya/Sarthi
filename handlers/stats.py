"""
Stats Handler
/stats command — Personal Progress Dashboard
- Weekly & Monthly study hours
- Subject-wise breakdown (heatmap style)
- Streak graph last 14 days
- Tasks completion rate
- Test score trend
- Study log entry (manual log if no timer used)
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn
from ui import back_btn, cancel_btn, subject_kb, E
from handlers.common import check_banned
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

# States
(LOG_SUBJECT, LOG_MINUTES) = range(2)

SUBJECT_EMOJI = {
    "PHY":   "⚛️",
    "CHEM":  "🧪",
    "MATH":  "📏",
    "BIO":   "🧬",
    "OTHER": "📌",
    "General": "📚",
}


def _uid(update: Update):
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE tg_id=?",
                       (update.effective_user.id,)).fetchone()
    conn.close()
    return row["id"] if row else None


def _bar(minutes: int, max_minutes: int, width: int = 10) -> str:
    """Generate a text progress bar."""
    if max_minutes == 0:
        filled = 0
    else:
        filled = round((minutes / max_minutes) * width)
    return "█" * filled + "░" * (width - filled)


def _mins_to_hrs(m: int) -> str:
    if m < 60:
        return f"{m}m"
    return f"{m // 60}h {m % 60}m" if m % 60 else f"{m // 60}h"


# ════════════════════════════════════════════════════════════════════════════
#  /stats COMMAND
# ════════════════════════════════════════════════════════════════════════════
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return
    kb = Markup([
        [Btn("📊 Weekly Stats",  callback_data="stats_weekly"),
         Btn("📅 Monthly Stats", callback_data="stats_monthly")],
        [Btn("📈 All Time",      callback_data="stats_alltime"),
         Btn("✍️ Log Study",     callback_data="stats_log_start")],
    ])
    await update.message.reply_text(
        "📊 *Your Progress Dashboard*\n\nSelect a view:",
        reply_markup=kb, parse_mode="Markdown"
    )


# Can also be triggered via callback (from home or elsewhere)
async def stats_home_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END
    kb = Markup([
        [Btn("📊 Weekly Stats",  callback_data="stats_weekly"),
         Btn("📅 Monthly Stats", callback_data="stats_monthly")],
        [Btn("📈 All Time",      callback_data="stats_alltime"),
         Btn("✍️ Log Study",     callback_data="stats_log_start")],
        [Btn(f"{E['back']} Back", callback_data="home")],
    ])
    await query.edit_message_text(
        "📊 *Your Progress Dashboard*\n\nSelect a view:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  WEEKLY STATS
# ════════════════════════════════════════════════════════════════════════════
async def stats_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    today = date.today()
    week_ago = (today - timedelta(days=6)).isoformat()
    today_str = today.isoformat()

    conn = get_conn()

    # Study log
    study_rows = conn.execute(
        """SELECT subject, SUM(minutes) as mins, date
           FROM study_log WHERE user_id=? AND date>=? AND date<=?
           GROUP BY subject ORDER BY mins DESC""",
        (uid, week_ago, today_str)
    ).fetchall()

    # Daily study per day (for streak graph)
    daily_study = conn.execute(
        """SELECT date, SUM(minutes) as mins
           FROM study_log WHERE user_id=? AND date>=? AND date<=?
           GROUP BY date""",
        (uid, week_ago, today_str)
    ).fetchall()
    daily_map = {r["date"]: r["mins"] for r in daily_study}

    # Tasks
    tasks_total = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND date>=?", (uid, week_ago)
    ).fetchone()[0]
    tasks_done = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND date>=? AND done=1", (uid, week_ago)
    ).fetchone()[0]

    # Streak
    user_row = conn.execute("SELECT streak FROM users WHERE tg_id=?",
                            (update.effective_user.id,)).fetchone()
    streak = user_row["streak"] if user_row else 0

    # Test scores this week
    scores = conn.execute(
        "SELECT * FROM test_scores WHERE user_id=? AND date>=? ORDER BY date DESC",
        (uid, week_ago)
    ).fetchall()

    conn.close()

    total_mins = sum(r["mins"] for r in study_rows)
    max_subj_mins = max((r["mins"] for r in study_rows), default=1)

    # Build streak graph — last 7 days
    streak_graph = ""
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        day_label = (today - timedelta(days=i)).strftime("%a")
        mins = daily_map.get(d, 0)
        dot = "🟩" if mins >= 30 else ("🟨" if mins > 0 else "⬜")
        streak_graph += f"{dot}"
    streak_graph += "  ← Today"

    # Subject breakdown with bars
    subj_lines = ""
    for r in study_rows:
        emoji = SUBJECT_EMOJI.get(r["subject"], "📚")
        bar = _bar(r["mins"], max_subj_mins, 8)
        subj_lines += f"{emoji} `{(r['subject'] or 'Other'):<6}` {bar} {_mins_to_hrs(r['mins'])}\n"
    if not subj_lines:
        subj_lines = "  No study logged this week.\n"

    # Test score summary
    score_text = ""
    if scores:
        for s in scores[:3]:
            score_text += f"  📝 {s['test_name']} — *{s['total']}* ({s['date']})\n"
    else:
        score_text = "  No tests this week.\n"

    # Task completion bar
    task_pct = round((tasks_done / tasks_total * 100)) if tasks_total else 0
    task_bar = _bar(tasks_done, tasks_total or 1, 10)

    text = (
        f"📊 *Weekly Stats*\n"
        f"_{(today - timedelta(days=6)).strftime('%d %b')} → {today.strftime('%d %b %Y')}_\n\n"
        f"🔥 *Streak:* {streak} day(s)\n"
        f"📅 *Activity (last 7 days):*\n{streak_graph}\n"
        f"🟩=30m+ 🟨=some ⬜=none\n\n"
        f"⏱️ *Total Study:* {_mins_to_hrs(total_mins)}\n\n"
        f"📚 *Subject Breakdown:*\n{subj_lines}\n"
        f"📝 *Tasks:* {task_bar} {tasks_done}/{tasks_total} ({task_pct}%)\n\n"
        f"🎯 *Test Scores:*\n{score_text}"
    )

    kb = Markup([
        [Btn("📅 Monthly Stats", callback_data="stats_monthly"),
         Btn("📈 All Time",      callback_data="stats_alltime")],
        [Btn("✍️ Log Study",     callback_data="stats_log_start"),
         Btn(f"{E['back']} Back", callback_data="stats_home")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  MONTHLY STATS
# ════════════════════════════════════════════════════════════════════════════
async def stats_monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    today = date.today()
    month_ago = (today - timedelta(days=29)).isoformat()
    today_str = today.isoformat()

    conn = get_conn()

    study_rows = conn.execute(
        """SELECT subject, SUM(minutes) as mins
           FROM study_log WHERE user_id=? AND date>=? AND date<=?
           GROUP BY subject ORDER BY mins DESC""",
        (uid, month_ago, today_str)
    ).fetchall()

    # Weekly breakdown (4 weeks)
    weekly_totals = []
    for w in range(3, -1, -1):
        w_start = (today - timedelta(days=(w+1)*7 - 1)).isoformat()
        w_end   = (today - timedelta(days=w*7)).isoformat()
        w_mins  = conn.execute(
            "SELECT SUM(minutes) FROM study_log WHERE user_id=? AND date>=? AND date<=?",
            (uid, w_start, w_end)
        ).fetchone()[0] or 0
        week_label = f"W{4-w}"
        weekly_totals.append((week_label, w_mins))

    tasks_total = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND date>=?", (uid, month_ago)
    ).fetchone()[0]
    tasks_done = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND date>=? AND done=1", (uid, month_ago)
    ).fetchone()[0]

    scores = conn.execute(
        "SELECT * FROM test_scores WHERE user_id=? AND date>=? ORDER BY date",
        (uid, month_ago)
    ).fetchall()

    # Active study days
    active_days = conn.execute(
        """SELECT COUNT(DISTINCT date) FROM study_log
           WHERE user_id=? AND date>=? AND minutes>0""",
        (uid, month_ago)
    ).fetchone()[0]

    conn.close()

    total_mins = sum(r["mins"] for r in study_rows)
    max_subj   = max((r["mins"] for r in study_rows), default=1)
    max_week   = max((m for _, m in weekly_totals), default=1)

    # Subject breakdown
    subj_lines = ""
    for r in study_rows:
        emoji = SUBJECT_EMOJI.get(r["subject"], "📚")
        bar   = _bar(r["mins"], max_subj, 8)
        subj_lines += f"{emoji} `{(r['subject'] or 'Other'):<6}` {bar} {_mins_to_hrs(r['mins'])}\n"
    if not subj_lines:
        subj_lines = "  No study logged this month.\n"

    # Weekly bars
    week_lines = ""
    for label, mins in weekly_totals:
        bar = _bar(mins, max_week, 8)
        week_lines += f"`{label}` {bar} {_mins_to_hrs(mins)}\n"

    # Score trend
    score_text = ""
    if scores:
        for s in scores[-5:]:
            score_text += f"  {s['date']} — *{s['total']}* ({s['test_name']})\n"
    else:
        score_text = "  No tests this month.\n"

    # Improvement: first vs last score
    improvement = ""
    if len(scores) >= 2:
        diff = scores[-1]["total"] - scores[0]["total"]
        arrow = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
        improvement = f"\n{arrow} Score change: *{'+' if diff>=0 else ''}{diff:.1f}* pts over {len(scores)} tests"

    task_pct = round((tasks_done / tasks_total * 100)) if tasks_total else 0

    text = (
        f"📅 *Monthly Stats*\n"
        f"_{(today - timedelta(days=29)).strftime('%d %b')} → {today.strftime('%d %b %Y')}_\n\n"
        f"⏱️ *Total Study:* {_mins_to_hrs(total_mins)}\n"
        f"📆 *Active Days:* {active_days}/30\n"
        f"📝 *Tasks:* {tasks_done}/{tasks_total} ({task_pct}%)\n\n"
        f"📚 *Subject Breakdown:*\n{subj_lines}\n"
        f"📊 *Weekly Progress:*\n{week_lines}\n"
        f"🎯 *Test Scores (last 5):*\n{score_text}{improvement}"
    )

    kb = Markup([
        [Btn("📊 Weekly Stats", callback_data="stats_weekly"),
         Btn("📈 All Time",     callback_data="stats_alltime")],
        [Btn("✍️ Log Study",    callback_data="stats_log_start"),
         Btn(f"{E['back']} Back", callback_data="stats_home")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ALL TIME STATS
# ════════════════════════════════════════════════════════════════════════════
async def stats_alltime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)

    conn = get_conn()

    study_rows = conn.execute(
        "SELECT subject, SUM(minutes) as mins FROM study_log WHERE user_id=? GROUP BY subject ORDER BY mins DESC",
        (uid,)
    ).fetchall()

    total_days = conn.execute(
        "SELECT COUNT(DISTINCT date) FROM study_log WHERE user_id=? AND minutes>0", (uid,)
    ).fetchone()[0]

    best_day = conn.execute(
        "SELECT date, SUM(minutes) as mins FROM study_log WHERE user_id=? GROUP BY date ORDER BY mins DESC LIMIT 1",
        (uid,)
    ).fetchone()

    tasks_done = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=1", (uid,)
    ).fetchone()[0]

    memories_count = conn.execute(
        "SELECT COUNT(*) FROM memories WHERE user_id=?", (uid,)
    ).fetchone()[0]

    scores = conn.execute(
        "SELECT * FROM test_scores WHERE user_id=? ORDER BY date", (uid,)
    ).fetchall()

    user_row = conn.execute("SELECT streak, joined FROM users WHERE tg_id=?",
                            (update.effective_user.id,)).fetchone()
    streak = user_row["streak"] if user_row else 0
    joined = user_row["joined"] if user_row else "N/A"
    conn.close()

    total_mins = sum(r["mins"] for r in study_rows)
    max_subj   = max((r["mins"] for r in study_rows), default=1)

    subj_lines = ""
    for r in study_rows:
        emoji = SUBJECT_EMOJI.get(r["subject"], "📚")
        bar   = _bar(r["mins"], max_subj, 8)
        pct   = round(r["mins"] / total_mins * 100) if total_mins else 0
        subj_lines += f"{emoji} `{(r['subject'] or 'Other'):<6}` {bar} {_mins_to_hrs(r['mins'])} ({pct}%)\n"
    if not subj_lines:
        subj_lines = "  No study logged yet.\n"

    best_day_text = f"{best_day['date']} — {_mins_to_hrs(best_day['mins'])}" if best_day else "N/A"

    # Score best/worst/avg
    score_text = ""
    if scores:
        totals = [s["total"] for s in scores]
        avg    = sum(totals) / len(totals)
        best   = max(totals)
        worst  = min(totals)
        score_text = (
            f"  Tests taken: {len(scores)}\n"
            f"  Best: *{best}* | Worst: *{worst}* | Avg: *{avg:.1f}*"
        )
    else:
        score_text = "  No tests recorded yet."

    text = (
        f"📈 *All Time Stats*\n"
        f"_Joined: {joined}_\n\n"
        f"🔥 *Best Streak:* {streak} days\n"
        f"⏱️ *Total Study:* {_mins_to_hrs(total_mins)}\n"
        f"📆 *Study Days:* {total_days}\n"
        f"🏆 *Best Day:* {best_day_text}\n"
        f"✅ *Tasks Done:* {tasks_done}\n"
        f"🧠 *Memories Saved:* {memories_count}\n\n"
        f"📚 *Subject Split:*\n{subj_lines}\n"
        f"🎯 *Test Performance:*\n{score_text}"
    )

    kb = Markup([
        [Btn("📊 Weekly",  callback_data="stats_weekly"),
         Btn("📅 Monthly", callback_data="stats_monthly")],
        [Btn("✍️ Log Study", callback_data="stats_log_start"),
         Btn(f"{E['back']} Back", callback_data="stats_home")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  MANUAL STUDY LOG (if timer not used)
# ════════════════════════════════════════════════════════════════════════════
async def log_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✍️ *Log Study Session*\n\nSelect subject:",
        reply_markup=Markup([
            [Btn("⚛️ PHY",  callback_data="slog_PHY"),
             Btn("🧪 CHEM", callback_data="slog_CHEM")],
            [Btn("📏 MATH", callback_data="slog_MATH"),
             Btn("🌿 BIO",  callback_data="slog_BIO")],
            [Btn("📌 OTHER", callback_data="slog_OTHER")],
            [Btn(f"{E['cancel']} Cancel", callback_data="stats_home")],
        ]),
        parse_mode="Markdown"
    )
    return LOG_SUBJECT


async def log_got_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["log_subject"] = query.data.replace("slog_", "")
    await query.edit_message_text(
        f"⏱️ How many minutes did you study *{context.user_data['log_subject']}*?\n\n"
        f"Send a number (e.g. `60` for 1 hour):",
        reply_markup=cancel_btn("stats_home"), parse_mode="Markdown"
    )
    return LOG_MINUTES


async def log_got_minutes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        mins = int(update.message.text.strip())
        assert 1 <= mins <= 720
    except (ValueError, AssertionError):
        await update.message.reply_text("❌ Enter a valid number (1-720):")
        return LOG_MINUTES

    uid  = _uid(update)
    subj = context.user_data.get("log_subject", "OTHER")
    conn = get_conn()
    conn.execute("INSERT INTO study_log (user_id, subject, minutes, date) VALUES (?,?,?,?)",
                 (uid, subj, mins, date.today().isoformat()))
    conn.commit()
    conn.close()

    emoji = SUBJECT_EMOJI.get(subj, "📚")
    await update.message.reply_text(
        f"✅ Logged *{_mins_to_hrs(mins)}* of {emoji} {subj}!\n\nKeep it up! 💪",
        reply_markup=Markup([
            [Btn("✍️ Log More",    callback_data="stats_log_start"),
             Btn("📊 View Stats", callback_data="stats_weekly")],
        ]),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "📊 *Stats Dashboard*",
            reply_markup=Markup([
                [Btn("📊 Weekly",  callback_data="stats_weekly"),
                 Btn("📅 Monthly", callback_data="stats_monthly")],
                [Btn("📈 All Time", callback_data="stats_alltime"),
                 Btn("✍️ Log Study", callback_data="stats_log_start")],
                [Btn(f"{E['back']} Back", callback_data="home")],
            ]),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_stats_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(stats_home_cb,     pattern="^stats_home$"),
            CallbackQueryHandler(stats_weekly,      pattern="^stats_weekly$"),
            CallbackQueryHandler(stats_monthly,     pattern="^stats_monthly$"),
            CallbackQueryHandler(stats_alltime,     pattern="^stats_alltime$"),
            CallbackQueryHandler(log_start,         pattern="^stats_log_start$"),
        ],
        states={
            LOG_SUBJECT: [CallbackQueryHandler(log_got_subject, pattern=r"^slog_(PHY|CHEM|MATH|BIO|OTHER)$")],
            LOG_MINUTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_got_minutes)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^stats_home$"),
            CommandHandler("stats", stats_cmd),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
