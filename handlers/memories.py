from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn
from ui import mem_home_kb, cancel_btn, back_btn, confirm_delete_kb, nav_kb, skip_btn, E
from handlers.common import check_banned
from datetime import date
import logging

logger = logging.getLogger(__name__)

# ── States ──────────────────────────────────────────────────────────────────
(
    MEM_TITLE, MEM_CONTENT, MEM_ANSWER, MEM_KEYPOINTS,
    REPORT_CONTENT,
) = range(5)


def _uid(update: Update):
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE tg_id=?",
                       (update.effective_user.id,)).fetchone()
    conn.close()
    return row["id"] if row else None


# ════════════════════════════════════════════════════════════════════════════
#  MEM HOME
# ════════════════════════════════════════════════════════════════════════════
async def mem_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END
    await query.edit_message_text(
        f"{E['memories']} *Memories*\n\nWhat would you like to save?",
        reply_markup=mem_home_kb(), parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ADD MEMORY — Silly / Error / Important
# ════════════════════════════════════════════════════════════════════════════
async def mem_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mem_type = query.data.replace("mem_", "")          # silly / error / important
    context.user_data["mem_draft"] = {"type": mem_type}
    labels = {"silly": "🤪 Silly Mistake", "error": "❗ Error", "important": "⭐ Important"}
    await query.edit_message_text(
        f"{labels.get(mem_type, 'Memory')} — Step 1\n\nEnter a *title* for this memory:",
        reply_markup=cancel_btn("mem_home"), parse_mode="Markdown"
    )
    return MEM_TITLE


async def mem_got_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return ConversationHandler.END
    context.user_data["mem_draft"]["title"] = update.message.text.strip()
    mem_type = context.user_data["mem_draft"]["type"]
    await update.message.reply_text(
        "Step 2 — Send the *content* (text or image/photo):",
        reply_markup=cancel_btn("mem_home"), parse_mode="Markdown"
    )
    return MEM_CONTENT


async def mem_got_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return ConversationHandler.END
    draft = context.user_data["mem_draft"]
    if update.message.photo:
        draft["file_id"] = update.message.photo[-1].file_id
        draft["file_type"] = "photo"
        draft["content"] = update.message.caption or ""
    else:
        draft["content"] = update.message.text.strip()
        draft["file_id"] = None
        draft["file_type"] = None

    if draft["type"] == "silly":
        # Save immediately
        return await _save_memory(update, context)
    else:
        # error / important — ask for answer
        await update.message.reply_text(
            "Step 3 — Send the *answer* (text or image) or skip:",
            reply_markup=Markup([
                [Btn("⏭️ Skip", callback_data="mem_skip_answer")],
                [Btn(f"{E['cancel']} Cancel", callback_data="mem_home")]
            ]), parse_mode="Markdown"
        )
        return MEM_ANSWER


async def mem_skip_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["mem_draft"]["answer"] = None
    context.user_data["mem_draft"]["ans_file"] = None
    context.user_data["mem_draft"]["ans_ftype"] = None
    await query.edit_message_text(
        "Step 4 — Enter *key points* (text) or skip:",
        reply_markup=Markup([
            [Btn("⏭️ Skip", callback_data="mem_skip_kp")],
            [Btn(f"{E['cancel']} Cancel", callback_data="mem_home")]
        ]), parse_mode="Markdown"
    )
    return MEM_KEYPOINTS


async def mem_got_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return ConversationHandler.END
    draft = context.user_data["mem_draft"]
    if update.message.photo:
        draft["ans_file"] = update.message.photo[-1].file_id
        draft["ans_ftype"] = "photo"
        draft["answer"] = update.message.caption or ""
    else:
        draft["answer"] = update.message.text.strip()
        draft["ans_file"] = None
        draft["ans_ftype"] = None
    await update.message.reply_text(
        "Step 4 — Enter *key points* (text) or skip:",
        reply_markup=Markup([
            [Btn("⏭️ Skip", callback_data="mem_skip_kp")],
            [Btn(f"{E['cancel']} Cancel", callback_data="mem_home")]
        ]), parse_mode="Markdown"
    )
    return MEM_KEYPOINTS


async def mem_skip_kp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["mem_draft"]["keypoints"] = None
    return await _save_memory(update, context)


async def mem_got_kp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return ConversationHandler.END
    context.user_data["mem_draft"]["keypoints"] = update.message.text.strip()
    return await _save_memory(update, context)


async def _save_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("mem_draft", {})
    uid = _uid(update)
    conn = get_conn()
    conn.execute(
        """INSERT INTO memories
           (user_id, mem_type, title, content, file_id, file_type,
            answer, ans_file, ans_ftype, keypoints)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (uid, d.get("type"), d.get("title"), d.get("content"),
         d.get("file_id"), d.get("file_type"),
         d.get("answer"), d.get("ans_file"), d.get("ans_ftype"),
         d.get("keypoints"))
    )
    conn.commit()
    conn.close()
    text = f"✅ Memory saved under *{d.get('type', '').capitalize()}*!"
    kb = Markup([[Btn(f"{E['back']} Back to Memories", callback_data="mem_home")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  VIEW MEMORIES — nav with Prev/Next
# ════════════════════════════════════════════════════════════════════════════
async def mem_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    # Pattern: mem_view_silly_0 OR mem_silly (first time)
    if query.data.startswith("mem_view_"):
        mem_type = parts[2]
        idx = int(parts[3])
    else:
        mem_type = parts[1]
        idx = 0

    uid = _uid(update)
    conn = get_conn()
    mems = conn.execute(
        "SELECT * FROM memories WHERE user_id=? AND mem_type=? ORDER BY created DESC",
        (uid, mem_type)
    ).fetchall()
    conn.close()

    if not mems:
        await query.edit_message_text(
            f"No {mem_type} memories yet!",
            reply_markup=back_btn("mem_home")
        )
        return ConversationHandler.END

    idx = max(0, min(idx, len(mems) - 1))
    m = mems[idx]
    label_map = {"silly": "🤪 Silly", "error": "❗ Error", "important": "⭐ Important"}
    text = (
        f"{label_map.get(mem_type, mem_type)} — *{m['title']}*\n"
        f"🗓 {m['created'][:10]}\n\n"
        f"{m['content'] or ''}"
    )
    extra_rows = []
    if mem_type in ("error", "important") and (m["answer"] or m["keypoints"]):
        extra_rows.append([Btn("📖 Answer & Key Points", callback_data=f"mem_ans_{mem_type}_{idx}")])
    extra_rows.append([Btn("🗑️ Delete this", callback_data=f"mem_del_confirm_{mem_type}_{m['id']}")])
    extra_rows.append([Btn(f"{E['back']} Back", callback_data="mem_home")])
    kb = nav_kb(f"mem_view_{mem_type}", idx, len(mems), extra_rows)

    if m["file_id"] and m["file_type"] == "photo":
        await query.message.delete()
        await context.bot.send_photo(
            update.effective_user.id,
            photo=m["file_id"],
            caption=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def mem_show_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    mem_type = parts[2]
    idx = int(parts[3])
    uid = _uid(update)
    conn = get_conn()
    mems = conn.execute(
        "SELECT * FROM memories WHERE user_id=? AND mem_type=? ORDER BY created DESC",
        (uid, mem_type)
    ).fetchall()
    conn.close()
    if not mems or idx >= len(mems):
        await query.answer("Not found.", show_alert=True)
        return ConversationHandler.END
    m = mems[idx]
    text = f"📖 *Answer:*\n{m['answer'] or 'N/A'}\n\n🔑 *Key Points:*\n{m['keypoints'] or 'N/A'}"
    kb = Markup([[Btn(f"{E['back']} Back to Entry", callback_data=f"mem_view_{mem_type}_{idx}")]])
    if m["ans_file"] and m["ans_ftype"] == "photo":
        await query.message.delete()
        await context.bot.send_photo(
            update.effective_user.id,
            photo=m["ans_file"],
            caption=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def mem_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    mem_type = parts[3]
    mem_id = int(parts[4])
    await query.edit_message_text(
        "⚠️ *This cannot be undone.* Delete this memory?",
        reply_markup=confirm_delete_kb(
            f"mem_del_yes_{mem_type}_{mem_id}",
            f"mem_view_{mem_type}_0"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def mem_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    mem_type = parts[3]
    mem_id = int(parts[4])
    conn = get_conn()
    conn.execute("DELETE FROM memories WHERE id=?", (mem_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text(
        "🗑️ Memory deleted.",
        reply_markup=back_btn("mem_home")
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  DAILY REPORT
# ════════════════════════════════════════════════════════════════════════════
async def daily_log_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    today_str = date.today().isoformat()
    conn = get_conn()
    today_report = conn.execute(
        "SELECT * FROM daily_reports WHERE user_id=? AND date=?", (uid, today_str)
    ).fetchone()
    conn.close()
    kb_rows = []
    if today_report:
        kb_rows.append([Btn("📒 See Today's Report", callback_data="report_view_today")])
    else:
        kb_rows.append([Btn("✍️ Write Today's Report", callback_data="report_write")])
    kb_rows.append([Btn("📚 Browse All Reports", callback_data="report_browse_0")])
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="mem_home")])
    await query.edit_message_text(
        f"📒 *Daily Report*\n\nDate: {today_str}",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def report_write_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✍️ *Write Today's Report*\n\nSend your report (text or image):",
        reply_markup=cancel_btn("daily_log_home"), parse_mode="Markdown"
    )
    return REPORT_CONTENT


async def report_got_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return ConversationHandler.END
    uid = _uid(update)
    today_str = date.today().isoformat()
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
        content = update.message.caption or ""
    else:
        content = update.message.text.strip()
        file_id = None
        file_type = None
    conn = get_conn()
    conn.execute(
        """INSERT INTO daily_reports (user_id, date, content, file_id, file_type)
           VALUES (?,?,?,?,?)
           ON CONFLICT(user_id, date) DO UPDATE SET
               content=excluded.content,
               file_id=excluded.file_id,
               file_type=excluded.file_type""",
        (uid, today_str, content, file_id, file_type)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        "✅ Today's report saved!",
        reply_markup=back_btn("daily_log_home")
    )
    return ConversationHandler.END


async def report_view_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    today_str = date.today().isoformat()
    conn = get_conn()
    r = conn.execute("SELECT * FROM daily_reports WHERE user_id=? AND date=?",
                     (uid, today_str)).fetchone()
    conn.close()
    if not r:
        await query.edit_message_text("No report for today yet.", reply_markup=back_btn("daily_log_home"))
        return ConversationHandler.END
    text = f"📒 *Daily Report — {r['date']}*\n\n{r['content'] or ''}"
    kb = Markup([
        [Btn("✍️ Update Report", callback_data="report_write")],
        [Btn(f"{E['back']} Back", callback_data="daily_log_home")]
    ])
    if r["file_id"] and r["file_type"] == "photo":
        await query.message.delete()
        await context.bot.send_photo(
            update.effective_user.id,
            photo=r["file_id"],
            caption=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def report_browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[-1])
    uid = _uid(update)
    conn = get_conn()
    reports = conn.execute(
        "SELECT * FROM daily_reports WHERE user_id=? ORDER BY date DESC", (uid,)
    ).fetchall()
    conn.close()
    if not reports:
        await query.edit_message_text("No reports yet.", reply_markup=back_btn("daily_log_home"))
        return ConversationHandler.END
    idx = max(0, min(idx, len(reports) - 1))
    r = reports[idx]
    text = f"📒 *Daily Report — {r['date']}*\n\n{r['content'] or ''}"
    extra = [[Btn(f"{E['back']} Back", callback_data="daily_log_home")]]
    kb = nav_kb("report_browse", idx, len(reports), extra)
    if r["file_id"] and r["file_type"] == "photo":
        await query.message.delete()
        await context.bot.send_photo(
            update.effective_user.id,
            photo=r["file_id"],
            caption=text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  CANCEL
# ════════════════════════════════════════════════════════════════════════════
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            f"{E['memories']} *Memories*",
            reply_markup=mem_home_kb(), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"{E['memories']} *Memories*",
            reply_markup=mem_home_kb(), parse_mode="Markdown"
        )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BUILD ConversationHandler
# ════════════════════════════════════════════════════════════════════════════
def build_mem_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(mem_home,         pattern="^mem_home$"),
            CallbackQueryHandler(mem_add_start,    pattern="^mem_(silly|error|important)$"),
            CallbackQueryHandler(mem_view,         pattern=r"^mem_view_(silly|error|important)_\d+$"),
            CallbackQueryHandler(mem_view,         pattern=r"^mem_(silly|error|important)$"),
            CallbackQueryHandler(mem_show_answer,  pattern=r"^mem_ans_(error|important)_\d+$"),
            CallbackQueryHandler(mem_del_confirm,  pattern=r"^mem_del_confirm_(silly|error|important)_\d+$"),
            CallbackQueryHandler(mem_del_yes,      pattern=r"^mem_del_yes_(silly|error|important)_\d+$"),
            CallbackQueryHandler(daily_log_home,   pattern="^daily_log_home$"),
            CallbackQueryHandler(report_write_start, pattern="^report_write$"),
            CallbackQueryHandler(report_view_today,  pattern="^report_view_today$"),
            CallbackQueryHandler(report_browse,    pattern=r"^report_browse_\d+$"),
        ],
        states={
            MEM_TITLE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, mem_got_title)],
            MEM_CONTENT:  [
                MessageHandler(filters.PHOTO, mem_got_content),
                MessageHandler(filters.TEXT & ~filters.COMMAND, mem_got_content),
            ],
            MEM_ANSWER:   [
                MessageHandler(filters.PHOTO, mem_got_answer),
                MessageHandler(filters.TEXT & ~filters.COMMAND, mem_got_answer),
                CallbackQueryHandler(mem_skip_answer, pattern="^mem_skip_answer$"),
            ],
            MEM_KEYPOINTS:[
                MessageHandler(filters.TEXT & ~filters.COMMAND, mem_got_kp),
                CallbackQueryHandler(mem_skip_kp, pattern="^mem_skip_kp$"),
            ],
            REPORT_CONTENT:[
                MessageHandler(filters.PHOTO, report_got_content),
                MessageHandler(filters.TEXT & ~filters.COMMAND, report_got_content),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^mem_home$"),
            CommandHandler("start", cancel),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
