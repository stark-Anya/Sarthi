import logging
import random
from datetime import datetime, date, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_conn, get_all_users
from config import TIMEZONE

logger = logging.getLogger(__name__)

MOTIVATIONAL_QUOTES = [
    "The secret of getting ahead is getting started. 🚀",
    "Success is the sum of small efforts, repeated day in and day out. 💪",
    "Don't watch the clock; do what it does. Keep going. ⏰",
    "You don't have to be great to start, but you have to start to be great. 🌟",
    "Believe you can and you're halfway there. ✨",
    "Hard work beats talent when talent doesn't work hard. 🔥",
    "Every expert was once a beginner. Keep going! 📚",
    "JEE is not just an exam — it's a test of your consistency. 💎",
]

IST = pytz.timezone(TIMEZONE)


async def job_lecture_alerts(app):
    now_str = datetime.now(IST).strftime("%H:%M")
    conn = get_conn()
    lectures = conn.execute(
        "SELECT l.*, u.tg_id FROM lectures l JOIN users u ON l.user_id=u.id "
        "WHERE l.alert_time=? AND l.active=1 AND u.is_banned=0",
        (now_str,)
    ).fetchall()
    conn.close()
    from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
    for lec in lectures:
        msg = lec["message"] or f"⏰ Time to watch your lecture!"
        text = (
            f"{msg}\n\n"
            f"🎥 *{lec['title']}*\n"
            f"📚 Subject: {lec['subject'] or 'N/A'}"
        )
        kb = Markup([
            [Btn("🔗 Open Link",      url=lec["link"]) if lec["link"] else Btn("No link", callback_data="noop"),
             Btn("👁️ Mark Watched",   callback_data=f"lec_watched_{lec['id']}")],
            [Btn("😴 Snooze 15 min", callback_data=f"lec_snooze_{lec['id']}"),
             Btn("⏱️ Start Timer",   callback_data="timer_home")],
        ])
        try:
            await app.bot.send_message(lec["tg_id"], text, reply_markup=kb, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Lecture alert error for {lec['tg_id']}: {e}")


async def job_morning_msg(app):
    users = get_all_users()
    today_str = date.today().strftime("%A, %d %B %Y")
    quote = random.choice(MOTIVATIONAL_QUOTES)
    from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
    kb = Markup([[Btn("📅 Open Today", callback_data="today_home")]])
    for u in users:
        conn = get_conn()
        row = conn.execute("SELECT streak FROM users WHERE tg_id=?", (u["tg_id"],)).fetchone()
        conn.close()
        streak = row["streak"] if row else 0
        text = (
            f"🌅 *Good Morning!*\n\n"
            f"📅 {today_str}\n"
            f"🔥 Streak: *{streak} day(s)*\n\n"
            f"💬 _{quote}_"
        )
        try:
            await app.bot.send_message(u["tg_id"], text, reply_markup=kb, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Morning msg error for {u['tg_id']}: {e}")


async def job_weekly_report(app):
    users = get_all_users()
    from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    for u in users:
        conn = get_conn()
        uid_row = conn.execute("SELECT id, streak FROM users WHERE tg_id=?", (u["tg_id"],)).fetchone()
        if not uid_row:
            conn.close()
            continue
        uid = uid_row["id"]
        streak = uid_row["streak"]
        tasks_done = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=1 AND date>=?", (uid, week_ago)
        ).fetchone()[0]
        tasks_total = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id=? AND date>=?", (uid, week_ago)
        ).fetchone()[0]
        study_rows = conn.execute(
            "SELECT subject, SUM(minutes) as mins FROM study_log WHERE user_id=? AND date>=? GROUP BY subject",
            (uid, week_ago)
        ).fetchall()
        conn.close()

        study_text = "\n".join([f"  • {r['subject']}: {r['mins']} min" for r in study_rows]) or "  No study logged."
        total_mins = sum(r["mins"] for r in study_rows)

        text = (
            f"📊 *Weekly Report*\n\n"
            f"📅 Last 7 days\n"
            f"🔥 Streak: *{streak} days*\n\n"
            f"📝 Tasks: {tasks_done}/{tasks_total} done\n"
            f"⏱️ Study Time: {total_mins} min\n\n"
            f"📚 By Subject:\n{study_text}"
        )
        try:
            await app.bot.send_message(u["tg_id"], text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Weekly report error for {u['tg_id']}: {e}")


async def job_revision_alerts(app):
    today_str = date.today().isoformat()
    conn = get_conn()
    rows = conn.execute(
        """SELECT r.*, u.tg_id FROM revision_schedule r
           JOIN users u ON r.user_id=u.id
           WHERE r.done=0 AND r.due_date<=? AND u.is_banned=0""",
        (today_str,)
    ).fetchall()
    conn.close()
    from collections import defaultdict
    user_revs = defaultdict(list)
    for r in rows:
        user_revs[r["tg_id"]].append(r)
    from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
    for tg_id, revs in user_revs.items():
        topics = "\n".join([f"• {r['topic']} ({r['due_date']})" for r in revs])
        text = f"🔄 *Revisions Due Today*\n\n{topics}"
        kb = Markup([[Btn("📅 Open Revisions", callback_data="revision_home")]])
        try:
            await app.bot.send_message(tg_id, text, reply_markup=kb, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Revision alert error for {tg_id}: {e}")


async def job_formula_flash(app):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM formulas WHERE content IS NOT NULL AND content != '' ORDER BY RANDOM() LIMIT 1"
    ).fetchall()
    conn.close()
    if not rows:
        return
    f = rows[0]
    users = get_all_users()
    from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
    kb = Markup([
        [Btn("✅ Got it!", callback_data="noop"),
         Btn("📐 Open Formulas", callback_data="formula_home")]
    ])
    text = f"🔢 *Formula Flash*\n\n📚 Chapter: {f['chapter']} (Class {f['class_num']})\n\n{f['content']}"
    for u in users:
        try:
            await app.bot.send_message(u["tg_id"], text, reply_markup=kb, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Formula flash error for {u['tg_id']}: {e}")


async def job_backup_db(app):
    """Send daily DB backup file to ADMIN_ID at 11:00 PM IST."""
    from config import ADMIN_ID, DB_PATH
    try:
        today = date.today().strftime("%d-%b-%Y")
        with open(DB_PATH, "rb") as f:
            await app.bot.send_document(
                ADMIN_ID,
                document=f,
                caption=f"🗄️ *Daily DB Backup*\n📅 {today}",
                parse_mode="Markdown"
            )
        logger.info(f"[Backup] DB backup sent to admin {ADMIN_ID}")
    except Exception as e:
        logger.error(f"[Backup] Failed: {e}")


def setup_scheduler(app):
    scheduler = AsyncIOScheduler(timezone=IST)

    # Every minute — lecture alerts
    scheduler.add_job(job_lecture_alerts, "cron", minute="*", args=[app])

    # 6:00 AM — morning message
    scheduler.add_job(job_morning_msg, "cron", hour=6, minute=0, args=[app])

    # Sunday 8:00 AM — weekly report
    scheduler.add_job(job_weekly_report, "cron", day_of_week="sun", hour=8, minute=0, args=[app])

    # 9:00 AM — revision alerts
    scheduler.add_job(job_revision_alerts, "cron", hour=9, minute=0, args=[app])

    # 7:00 AM — formula flash
    scheduler.add_job(job_formula_flash, "cron", hour=7, minute=0, args=[app])

    # 11:00 PM — daily DB backup to admin
    scheduler.add_job(job_backup_db, "cron", hour=23, minute=0, args=[app])

    scheduler.start()
    logger.info("[Scheduler] All jobs started.")
