import asyncio
from datetime import date, datetime, timedelta
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn, get_user, update_streak
from ui import (today_home_kb, cancel_btn, back_btn, confirm_delete_kb,
                subject_kb, timer_kb, nav_kb, E)
from handlers.common import check_banned
import logging

logger = logging.getLogger(__name__)

# ── States ──────────────────────────────────────────────────────────────────
(
    TASK_TEXT, TASK_LIST,
    LEC_TITLE, LEC_LINK, LEC_SUBJ, LEC_TIME, LEC_MSG,
    LEC_EDIT_FIELD, LEC_EDIT_VAL,
    TIMER_CUSTOM,
    SCORE_NAME, SCORE_PHY, SCORE_CHEM, SCORE_MATH,
    DOUBT_TEXT, DOUBT_SUBJ,
) = range(16)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _uid(update: Update):
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE tg_id=?",
                       (update.effective_user.id,)).fetchone()
    conn.close()
    return row["id"] if row else None


def _today():
    return date.today().isoformat()


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY — Today Home
# ════════════════════════════════════════════════════════════════════════════
async def today_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END
    await query.edit_message_text(
        f"{E['today']} *Today's Dashboard*\n\nChoose an option:",
        reply_markup=today_home_kb(), parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  TASKS
# ════════════════════════════════════════════════════════════════════════════
async def task_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 *Add Task*\n\nSend task text. Optionally prefix with subject:\n"
        "`PHY: Waves chapter`\n`CHEM: p-block`\n`MATH: Integration`",
        reply_markup=cancel_btn("today_home"), parse_mode="Markdown"
    )
    return TASK_TEXT


async def task_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return ConversationHandler.END
    text = update.message.text.strip()
    subject = None
    for prefix in ["PHY:", "CHEM:", "MATH:", "BIO:", "OTHER:"]:
        if text.upper().startswith(prefix):
            subject = prefix.rstrip(":")
            text = text[len(prefix):].strip()
            break
    uid = _uid(update)
    conn = get_conn()
    conn.execute("INSERT INTO tasks (user_id, text, subject, date) VALUES (?,?,?,?)",
                 (uid, text, subject, _today()))
    conn.commit()
    conn.close()
    subj_label = f" [{subject}]" if subject else ""
    await update.message.reply_text(
        f"✅ Task added{subj_label}: *{text}*\n\nAdd another or go back.",
        reply_markup=Markup([
            [Btn("➕ Add Another", callback_data="task_add"),
             Btn(f"{E['back']} Today", callback_data="today_home")]
        ]), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def task_list_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END
    uid = _uid(update)
    conn = get_conn()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=? AND date=? ORDER BY done ASC, id DESC",
        (uid, _today())
    ).fetchall()
    conn.close()
    if not tasks:
        await query.edit_message_text(
            "📝 No tasks for today yet!",
            reply_markup=Markup([
                [Btn("➕ Add Task", callback_data="task_add")],
                [Btn(f"{E['back']} Back", callback_data="today_home")]
            ])
        )
        return ConversationHandler.END

    rows = []
    for t in tasks:
        tick = "✅" if t["done"] else "⬜"
        label = f"{tick} {t['text']}"
        if t["subject"]:
            label = f"{tick} [{t['subject']}] {t['text']}"
        rows.append([Btn(label, callback_data=f"task_toggle_{t['id']}")])
    rows.append([Btn("🗑️ Delete a task", callback_data="task_delete_pick")])
    rows.append([Btn(f"{E['back']} Back", callback_data="today_home")])
    done_count = sum(1 for t in tasks if t["done"])
    await query.edit_message_text(
        f"📝 *Today's Tasks* ({done_count}/{len(tasks)} done)",
        reply_markup=Markup(rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def task_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[-1])
    conn = get_conn()
    row = conn.execute("SELECT done FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row:
        new_done = 0 if row["done"] else 1
        conn.execute("UPDATE tasks SET done=? WHERE id=?", (new_done, task_id))
        conn.commit()
        if new_done:
            update_streak(update.effective_user.id)
    conn.close()
    await task_list_show(update, context)


async def task_delete_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    conn = get_conn()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=? AND date=?", (uid, _today())
    ).fetchall()
    conn.close()
    if not tasks:
        await query.edit_message_text("No tasks to delete.",
                                      reply_markup=back_btn("task_list"))
        return ConversationHandler.END
    rows = [[Btn(t["text"][:40], callback_data=f"task_del_confirm_{t['id']}")] for t in tasks]
    rows.append([Btn(f"{E['back']} Back", callback_data="task_list")])
    await query.edit_message_text("Select task to delete:", reply_markup=Markup(rows))
    return ConversationHandler.END


async def task_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[-1])
    context.user_data["del_task_id"] = task_id
    await query.edit_message_text(
        "⚠️ *This cannot be undone.* Delete this task?",
        reply_markup=confirm_delete_kb(f"task_del_yes_{task_id}", "task_list"),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def task_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[-1])
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text("🗑️ Task deleted.", reply_markup=back_btn("task_list"))
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  LECTURES
# ════════════════════════════════════════════════════════════════════════════
async def lec_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("lec_draft", None)
    await query.edit_message_text(
        f"{E['lecture']} *Add Lecture*\n\nStep 1/5 — Enter lecture title:",
        reply_markup=cancel_btn("today_home"), parse_mode="Markdown"
    )
    return LEC_TITLE


async def lec_got_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lec_draft"] = {"title": update.message.text.strip()}
    await update.message.reply_text(
        "Step 2/5 — Send the lecture link (URL):",
        reply_markup=cancel_btn("today_home")
    )
    return LEC_LINK


async def lec_got_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lec_draft"]["link"] = update.message.text.strip()
    await update.message.reply_text(
        "Step 3/5 — Choose subject:",
        reply_markup=subject_kb("lec_subj")
    )
    return LEC_SUBJ


async def lec_got_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subj = query.data.replace("lec_subj_", "")
    context.user_data["lec_draft"]["subject"] = subj
    await query.edit_message_text(
        "Step 4/5 — Enter alert time (HH:MM, 24h format, e.g. `18:30`):",
        reply_markup=cancel_btn("today_home"), parse_mode="Markdown"
    )
    return LEC_TIME


async def lec_got_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.strip()
    try:
        datetime.strptime(t, "%H:%M")
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Use HH:MM (e.g. `18:30`):",
                                        parse_mode="Markdown")
        return LEC_TIME
    context.user_data["lec_draft"]["alert_time"] = t
    await update.message.reply_text(
        "Step 5/5 — Enter a custom reminder message (optional):",
        reply_markup=Markup([
            [Btn("⏭️ Skip", callback_data="lec_skip_msg")],
            [Btn(f"{E['cancel']} Cancel", callback_data="today_home")]
        ])
    )
    return LEC_MSG


async def lec_skip_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["lec_draft"]["message"] = None
    return await _save_lecture(update, context)


async def lec_got_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lec_draft"]["message"] = update.message.text.strip()
    return await _save_lecture(update, context)


async def _save_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("lec_draft", {})
    uid = _uid(update)
    conn = get_conn()
    conn.execute(
        "INSERT INTO lectures (user_id, title, link, subject, alert_time, message) VALUES (?,?,?,?,?,?)",
        (uid, d.get("title"), d.get("link"), d.get("subject"), d.get("alert_time"), d.get("message"))
    )
    conn.commit()
    conn.close()
    msg_target = update.callback_query or update.message
    text = f"✅ Lecture *{d.get('title')}* saved!\nAlert at {d.get('alert_time')} IST."
    kb = Markup([[Btn(f"{E['back']} Today", callback_data="today_home")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def lec_list_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    conn = get_conn()
    lecs = conn.execute(
        "SELECT * FROM lectures WHERE user_id=? AND active=1 ORDER BY alert_time ASC",
        (uid,)
    ).fetchall()
    conn.close()
    if not lecs:
        await query.edit_message_text(
            "🎥 No lectures saved yet!",
            reply_markup=Markup([
                [Btn("➕ Add Lecture", callback_data="lec_add")],
                [Btn(f"{E['back']} Back", callback_data="today_home")]
            ])
        )
        return ConversationHandler.END
    rows = [[Btn(f"🎥 {l['title']} [{l['alert_time']}]", callback_data=f"lec_view_{l['id']}")] for l in lecs]
    rows.append([Btn(f"{E['back']} Back", callback_data="today_home")])
    await query.edit_message_text("🎥 *Your Lectures:*", reply_markup=Markup(rows), parse_mode="Markdown")
    return ConversationHandler.END


async def lec_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lec_id = int(query.data.split("_")[-1])
    context.user_data["lec_view_id"] = lec_id
    conn = get_conn()
    lec = conn.execute("SELECT * FROM lectures WHERE id=?", (lec_id,)).fetchone()
    conn.close()
    if not lec:
        await query.edit_message_text("Lecture not found.", reply_markup=back_btn("lec_list"))
        return ConversationHandler.END
    text = (
        f"🎥 *{lec['title']}*\n"
        f"📚 Subject: {lec['subject'] or 'N/A'}\n"
        f"⏰ Alert: {lec['alert_time'] or 'N/A'}\n"
        f"🔗 Link: {lec['link'] or 'N/A'}\n"
        f"💬 Message: {lec['message'] or 'None'}"
    )
    kb = Markup([
        [Btn("✏️ Edit Title", callback_data=f"lec_edit_title_{lec_id}"),
         Btn("✏️ Edit Link",  callback_data=f"lec_edit_link_{lec_id}")],
        [Btn("✏️ Edit Time",  callback_data=f"lec_edit_time_{lec_id}"),
         Btn("✏️ Edit Msg",   callback_data=f"lec_edit_msg_{lec_id}")],
        [Btn(f"{E['watch']} Mark Watched", callback_data=f"lec_watched_{lec_id}"),
         Btn("🗑️ Delete",                  callback_data=f"lec_del_confirm_{lec_id}")],
        [Btn(f"{E['back']} Back", callback_data="lec_list")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def lec_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    field = parts[2]
    lec_id = int(parts[3])
    context.user_data["lec_edit"] = {"field": field, "lec_id": lec_id}
    field_labels = {"title": "new title", "link": "new link", "time": "new time (HH:MM)", "msg": "new message"}
    await query.edit_message_text(
        f"✏️ Enter {field_labels.get(field, 'new value')}:",
        reply_markup=cancel_btn(f"lec_view_{lec_id}")
    )
    return LEC_EDIT_VAL


async def lec_edit_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    info = context.user_data.get("lec_edit", {})
    field_map = {"title": "title", "link": "link", "time": "alert_time", "msg": "message"}
    col = field_map.get(info.get("field"))
    lec_id = info.get("lec_id")
    if col and lec_id:
        conn = get_conn()
        conn.execute(f"UPDATE lectures SET {col}=? WHERE id=?", (val, lec_id))
        conn.commit()
        conn.close()
    await update.message.reply_text(
        "✅ Updated!",
        reply_markup=Markup([[Btn("👁️ Back to Lecture", callback_data=f"lec_view_{lec_id}")]])
    )
    return ConversationHandler.END


async def lec_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lec_id = int(query.data.split("_")[-1])
    await query.edit_message_text(
        "⚠️ *This cannot be undone.* Delete this lecture?",
        reply_markup=confirm_delete_kb(f"lec_del_yes_{lec_id}", f"lec_view_{lec_id}"),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def lec_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lec_id = int(query.data.split("_")[-1])
    conn = get_conn()
    conn.execute("UPDATE lectures SET active=0 WHERE id=?", (lec_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text("🗑️ Lecture deleted.", reply_markup=back_btn("lec_list"))
    return ConversationHandler.END


async def lec_watched(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Marked as watched!")
    lec_id = int(query.data.split("_")[-1])
    uid = _uid(update)
    conn = get_conn()
    lec = conn.execute("SELECT * FROM lectures WHERE id=?", (lec_id,)).fetchone()
    if lec:
        today = date.today()
        for days in [1, 3, 7, 30]:
            due = (today + timedelta(days=days)).isoformat()
            conn.execute(
                "INSERT INTO revision_schedule (user_id, lecture_id, topic, due_date) VALUES (?,?,?,?)",
                (uid, lec_id, lec["title"], due)
            )
        conn.commit()
    conn.close()
    await query.edit_message_text(
        f"✅ *{lec['title']}* marked watched!\n\n"
        "📅 Revision reminders set for: 1 day, 3 days, 7 days, 30 days.",
        reply_markup=back_btn("lec_list"), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def lec_snooze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("😴 Snoozed for 15 min!")
    lec_id = int(query.data.split("_")[-1])
    conn = get_conn()
    lec = conn.execute("SELECT * FROM lectures WHERE id=?", (lec_id,)).fetchone()
    conn.close()
    if lec:
        async def send_snooze():
            await asyncio.sleep(900)
            try:
                await context.bot.send_message(
                    update.effective_user.id,
                    f"⏰ Snooze over! Time to watch: *{lec['title']}*\n🔗 {lec['link']}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Snooze send error: {e}")
        asyncio.create_task(send_snooze())


# ════════════════════════════════════════════════════════════════════════════
#  FOCUS TIMER
# ════════════════════════════════════════════════════════════════════════════
async def timer_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"{E['timer']} *Focus Timer*\n\nChoose duration:",
        reply_markup=timer_kb(), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def timer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    minutes = int(parts[1])
    await _run_timer(update, context, minutes)
    return ConversationHandler.END


async def timer_custom_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⏱️ Enter custom duration in minutes (e.g. `45`):",
        reply_markup=cancel_btn("timer_home"), parse_mode="Markdown"
    )
    return TIMER_CUSTOM


async def timer_custom_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        minutes = int(update.message.text.strip())
        assert 1 <= minutes <= 300
    except (ValueError, AssertionError):
        await update.message.reply_text("❌ Enter a number between 1 and 300.")
        return TIMER_CUSTOM
    await _run_timer(update, context, minutes)
    return ConversationHandler.END


async def _run_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, minutes: int):
    uid_tg = update.effective_user.id
    msg_target = update.callback_query or update.message
    text = f"⏱️ Timer started: *{minutes} minutes*\nI'll notify you when done. Go focus! 💪"
    kb = Markup([[Btn(f"{E['back']} Today", callback_data="today_home")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    async def _timer_task():
        await asyncio.sleep(minutes * 60)
        uid = _uid(update)
        subj = context.user_data.get("timer_subject", "General")
        conn = get_conn()
        conn.execute("INSERT INTO study_log (user_id, subject, minutes, date) VALUES (?,?,?,?)",
                     (uid, subj, minutes, _today()))
        conn.commit()
        conn.close()
        try:
            await context.bot.send_message(
                uid_tg,
                f"✅ *{minutes} min session complete!* Great work!\n"
                f"📊 Logged {minutes} min of study.",
                reply_markup=Markup([
                    [Btn("🔁 Another Round", callback_data="timer_home"),
                     Btn(f"{E['today']} Today", callback_data="today_home")]
                ]),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Timer done send error: {e}")

    asyncio.create_task(_timer_task())


# ════════════════════════════════════════════════════════════════════════════
#  TEST SCORES
# ════════════════════════════════════════════════════════════════════════════
async def score_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM test_scores WHERE user_id=? ORDER BY date DESC LIMIT 5", (uid,)
    ).fetchall()
    conn.close()
    text = f"{E['score']} *Test Scores*\n\n"
    if rows:
        for r in rows:
            text += f"📝 *{r['test_name']}* — {r['date']}\n  P:{r['phy']} C:{r['chem']} M:{r['math']} → *{r['total']}*\n"
    else:
        text += "No scores yet.\n"
    kb = Markup([
        [Btn("➕ Add Score", callback_data="score_add")],
        [Btn(f"{E['back']} Back", callback_data="today_home")]
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def score_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 *Add Test Score*\n\nEnter test name:",
        reply_markup=cancel_btn("score_home"), parse_mode="Markdown"
    )
    return SCORE_NAME


async def score_got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["score_draft"] = {"name": update.message.text.strip()}
    await update.message.reply_text("Enter Physics score:", reply_markup=cancel_btn("score_home"))
    return SCORE_PHY


async def score_got_phy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["score_draft"]["phy"] = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number for Physics:")
        return SCORE_PHY
    await update.message.reply_text("Enter Chemistry score:", reply_markup=cancel_btn("score_home"))
    return SCORE_CHEM


async def score_got_chem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["score_draft"]["chem"] = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number for Chemistry:")
        return SCORE_CHEM
    await update.message.reply_text("Enter Mathematics score:", reply_markup=cancel_btn("score_home"))
    return SCORE_MATH


async def score_got_math(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        math_score = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a valid number for Math:")
        return SCORE_MATH
    d = context.user_data["score_draft"]
    d["math"] = math_score
    total = d["phy"] + d["chem"] + d["math"]
    uid = _uid(update)
    conn = get_conn()
    conn.execute(
        "INSERT INTO test_scores (user_id, test_name, phy, chem, math, total, date) VALUES (?,?,?,?,?,?,?)",
        (uid, d["name"], d["phy"], d["chem"], d["math"], total, _today())
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Score saved!\n\n*{d['name']}*\nP:{d['phy']} C:{d['chem']} M:{d['math']}\n🎯 Total: *{total}*",
        reply_markup=back_btn("score_home"), parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  DOUBTS
# ════════════════════════════════════════════════════════════════════════════
async def doubt_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    conn = get_conn()
    doubts = conn.execute(
        "SELECT * FROM doubts WHERE user_id=? AND resolved=0 ORDER BY created DESC", (uid,)
    ).fetchall()
    conn.close()
    kb_rows = [[Btn(f"❓ {d['text'][:40]}", callback_data=f"doubt_resolve_{d['id']}")] for d in doubts]
    kb_rows.append([Btn("➕ Add Doubt", callback_data="doubt_add")])
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="today_home")])
    text = f"❓ *Doubts* ({len(doubts)} unresolved)" if doubts else "❓ *Doubts*\n\nNo pending doubts!"
    await query.edit_message_text(text, reply_markup=Markup(kb_rows), parse_mode="Markdown")
    return ConversationHandler.END


async def doubt_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ *Add Doubt*\n\nDescribe your doubt:",
        reply_markup=cancel_btn("doubt_home"), parse_mode="Markdown"
    )
    return DOUBT_TEXT


async def doubt_got_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["doubt_text"] = update.message.text.strip()
    await update.message.reply_text(
        "Choose subject for this doubt:",
        reply_markup=subject_kb("doubt_subj")
    )
    return DOUBT_SUBJ


async def doubt_got_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subj = query.data.replace("doubt_subj_", "")
    uid = _uid(update)
    conn = get_conn()
    conn.execute("INSERT INTO doubts (user_id, subject, text) VALUES (?,?,?)",
                 (uid, subj, context.user_data.get("doubt_text", "")))
    conn.commit()
    conn.close()
    await query.edit_message_text(
        f"✅ Doubt saved under *{subj}*!",
        reply_markup=back_btn("doubt_home"), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def doubt_resolve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Marked resolved!")
    doubt_id = int(query.data.split("_")[-1])
    conn = get_conn()
    conn.execute("UPDATE doubts SET resolved=1 WHERE id=?", (doubt_id,))
    conn.commit()
    conn.close()
    await doubt_home(update, context)


# ════════════════════════════════════════════════════════════════════════════
#  REVISIONS
# ════════════════════════════════════════════════════════════════════════════
async def revision_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    conn = get_conn()
    revs = conn.execute(
        "SELECT * FROM revision_schedule WHERE user_id=? AND done=0 AND due_date<=? ORDER BY due_date ASC",
        (uid, _today())
    ).fetchall()
    conn.close()
    if not revs:
        await query.edit_message_text(
            "🔄 No revisions due today!",
            reply_markup=back_btn("today_home")
        )
        return ConversationHandler.END
    rows = [[Btn(f"🔄 {r['topic'][:40]} ({r['due_date']})", callback_data=f"rev_done_{r['id']}")] for r in revs]
    rows.append([Btn(f"{E['back']} Back", callback_data="today_home")])
    await query.edit_message_text(
        f"🔄 *Revisions Due Today* ({len(revs)})\n\nTap to mark done:",
        reply_markup=Markup(rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def revision_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Revision done!")
    rev_id = int(query.data.split("_")[-1])
    conn = get_conn()
    conn.execute("UPDATE revision_schedule SET done=1 WHERE id=?", (rev_id,))
    conn.commit()
    conn.close()
    await revision_home(update, context)


# ════════════════════════════════════════════════════════════════════════════
#  CANCEL fallback
# ════════════════════════════════════════════════════════════════════════════
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f"{E['today']} *Today's Dashboard*",
            reply_markup=today_home_kb(), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"{E['today']} *Today's Dashboard*",
            reply_markup=today_home_kb(), parse_mode="Markdown"
        )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BUILD ConversationHandler — called from bot.py
# ════════════════════════════════════════════════════════════════════════════
def build_today_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(today_home,        pattern="^today_home$"),
            CallbackQueryHandler(task_add_start,    pattern="^task_add$"),
            CallbackQueryHandler(task_list_show,    pattern="^task_list$"),
            CallbackQueryHandler(task_delete_pick,  pattern="^task_delete_pick$"),
            CallbackQueryHandler(lec_add_start,     pattern="^lec_add$"),
            CallbackQueryHandler(lec_list_show,     pattern="^lec_list$"),
            CallbackQueryHandler(lec_view,          pattern=r"^lec_view_\d+$"),
            CallbackQueryHandler(lec_edit_start,    pattern=r"^lec_edit_(title|link|time|msg)_\d+$"),
            CallbackQueryHandler(lec_del_confirm,   pattern=r"^lec_del_confirm_\d+$"),
            CallbackQueryHandler(lec_del_yes,       pattern=r"^lec_del_yes_\d+$"),
            CallbackQueryHandler(lec_watched,       pattern=r"^lec_watched_\d+$"),
            CallbackQueryHandler(lec_snooze,        pattern=r"^lec_snooze_\d+$"),
            CallbackQueryHandler(timer_home,        pattern="^timer_home$"),
            CallbackQueryHandler(timer_start,       pattern=r"^timer_(25|50|15)$"),
            CallbackQueryHandler(timer_custom_ask,  pattern="^timer_custom$"),
            CallbackQueryHandler(score_home,        pattern="^score_home$"),
            CallbackQueryHandler(score_add_start,   pattern="^score_add$"),
            CallbackQueryHandler(doubt_home,        pattern="^doubt_home$"),
            CallbackQueryHandler(doubt_add_start,   pattern="^doubt_add$"),
            CallbackQueryHandler(doubt_resolve,     pattern=r"^doubt_resolve_\d+$"),
            CallbackQueryHandler(revision_home,     pattern="^revision_home$"),
            CallbackQueryHandler(revision_done,     pattern=r"^rev_done_\d+$"),
            CallbackQueryHandler(task_toggle,       pattern=r"^task_toggle_\d+$"),
            CallbackQueryHandler(task_del_confirm,  pattern=r"^task_del_confirm_\d+$"),
            CallbackQueryHandler(task_del_yes,      pattern=r"^task_del_yes_\d+$"),
        ],
        states={
            TASK_TEXT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, task_text_received)],
            LEC_TITLE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, lec_got_title)],
            LEC_LINK:      [MessageHandler(filters.TEXT & ~filters.COMMAND, lec_got_link)],
            LEC_SUBJ:      [CallbackQueryHandler(lec_got_subj, pattern=r"^lec_subj_")],
            LEC_TIME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, lec_got_time)],
            LEC_MSG:       [
                MessageHandler(filters.TEXT & ~filters.COMMAND, lec_got_msg),
                CallbackQueryHandler(lec_skip_msg, pattern="^lec_skip_msg$"),
            ],
            LEC_EDIT_VAL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, lec_edit_save)],
            TIMER_CUSTOM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, timer_custom_recv)],
            SCORE_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, score_got_name)],
            SCORE_PHY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, score_got_phy)],
            SCORE_CHEM:    [MessageHandler(filters.TEXT & ~filters.COMMAND, score_got_chem)],
            SCORE_MATH:    [MessageHandler(filters.TEXT & ~filters.COMMAND, score_got_math)],
            DOUBT_TEXT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, doubt_got_text)],
            DOUBT_SUBJ:    [CallbackQueryHandler(doubt_got_subj, pattern=r"^doubt_subj_")],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^today_home$"),
            CommandHandler("start", cancel),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
