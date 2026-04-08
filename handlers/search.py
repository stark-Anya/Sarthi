"""
Search Handler — /search <query>
Search memories, reports, formulas.
Each memory result has a Delete button.
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import get_conn
from handlers.common import check_banned
from ui import confirm_delete_kb, back_btn, E
import logging

logger = logging.getLogger(__name__)


def _uid(update: Update):
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE tg_id=?",
                       (update.effective_user.id,)).fetchone()
    conn.close()
    return row["id"] if row else None


async def search_cmd(update: Update, context):
    if await check_banned(update):
        return
    if not context.args:
        await update.message.reply_text(
            "🔍 Usage: `/search <query>`\n\nExample: `/search integration`",
            parse_mode="Markdown"
        )
        return

    query_str = " ".join(context.args).strip().lower()
    uid = _uid(update)
    conn = get_conn()

    memories = conn.execute(
        """SELECT * FROM memories
           WHERE user_id=? AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)
           ORDER BY created DESC LIMIT 10""",
        (uid, f"%{query_str}%", f"%{query_str}%")
    ).fetchall()

    reports = conn.execute(
        """SELECT * FROM daily_reports
           WHERE user_id=? AND (LOWER(date) LIKE ? OR LOWER(content) LIKE ?)
           ORDER BY date DESC LIMIT 5""",
        (uid, f"%{query_str}%", f"%{query_str}%")
    ).fetchall()

    formulas = conn.execute(
        """SELECT DISTINCT class_num, chapter, subject FROM formulas
           WHERE LOWER(chapter) LIKE ?
           ORDER BY class_num, chapter LIMIT 10""",
        (f"%{query_str}%",)
    ).fetchall()

    books = conn.execute(
        """SELECT * FROM books
           WHERE LOWER(book_name) LIKE ? OR LOWER(subject) LIKE ?
           ORDER BY class_num, subject, book_name LIMIT 10""",
        (f"%{query_str}%", f"%{query_str}%")
    ).fetchall()

    conn.close()

    if not memories and not reports and not formulas and not books:
        await update.message.reply_text(
            f"🔍 No results found for *{query_str}*.", parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"🔍 *Search results for:* `{query_str}`", parse_mode="Markdown"
    )

    # ── Memory results ──
    if memories:
        await update.message.reply_text(f"🧠 *Memories ({len(memories)}):*", parse_mode="Markdown")
        label_map = {"silly": "🤪", "error": "❗", "important": "⭐"}
        for m in memories:
            emoji = label_map.get(m["mem_type"], "📌")
            text  = f"{emoji} *{m['title']}*\n{m['created'][:10]}\n{(m['content'] or '')[:200]}"
            kb_rows = []
            if m["mem_type"] in ("error", "important") and (m["answer"] or m["keypoints"]):
                kb_rows.append([Btn("📖 Answer & Key Points",
                                    callback_data=f"search_ans_{m['mem_type']}_{m['id']}")])
            kb_rows.append([Btn("🗑️ Delete", callback_data=f"search_del_confirm_{m['mem_type']}_{m['id']}")])
            kb = Markup(kb_rows) if kb_rows else None
            if m["file_id"] and m["file_type"] == "photo":
                await context.bot.send_photo(
                    update.effective_user.id,
                    photo=m["file_id"], caption=text, reply_markup=kb, parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    # ── Report results ──
    if reports:
        await update.message.reply_text(f"📒 *Daily Reports ({len(reports)}):*", parse_mode="Markdown")
        for r in reports:
            text = f"📒 *{r['date']}*\n{(r['content'] or '')[:300]}"
            if r["file_id"] and r["file_type"] == "photo":
                await context.bot.send_photo(
                    update.effective_user.id,
                    photo=r["file_id"], caption=text, parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(text, parse_mode="Markdown")

    # ── Formula results ──
    if formulas:
        rows = [
            [Btn(f"📐 Class {f['class_num']}: {f['chapter']}",
                 callback_data=f"fchap_{f['class_num']}_{f['subject']}_{f['chapter']}")]
            for f in formulas
        ]
        await update.message.reply_text(
            f"📐 *Formula Chapters ({len(formulas)}):*",
            reply_markup=Markup(rows), parse_mode="Markdown"
        )

    # ── Books results ── (1 per row so full name is visible)
    if books:
        rows = [
            [Btn(f"📖 {b['book_name']} — Class {b['class_num']} | {b['subject']}",
                 callback_data=f"books_open_{b['id']}")]
            for b in books
        ]
        await update.message.reply_text(
            f"📚 *Books ({len(books)}):*",
            reply_markup=Markup(rows), parse_mode="Markdown"
        )


# ── Show answer from search result ──────────────────────────────────────────
async def search_show_answer(update: Update, context):
    query = update.callback_query
    await query.answer()
    parts    = query.data.split("_")
    mem_type = parts[2]
    mem_id   = int(parts[3])
    conn = get_conn()
    m = conn.execute("SELECT * FROM memories WHERE id=?", (mem_id,)).fetchone()
    conn.close()
    if not m:
        await query.answer("Not found.", show_alert=True)
        return
    text = f"📖 *Answer:*\n{m['answer'] or 'N/A'}\n\n🔑 *Key Points:*\n{m['keypoints'] or 'N/A'}"
    if m["ans_file"] and m["ans_ftype"] == "photo":
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_photo(
            update.effective_user.id,
            photo=m["ans_file"], caption=text, parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(text, parse_mode="Markdown")


# ── Delete from search result ────────────────────────────────────────────────
async def search_del_confirm(update: Update, context):
    query = update.callback_query
    await query.answer()
    parts    = query.data.split("_")
    mem_type = parts[3]
    mem_id   = int(parts[4])
    await query.edit_message_text(
        "⚠️ *This cannot be undone.* Delete this memory?",
        reply_markup=confirm_delete_kb(
            f"search_del_yes_{mem_type}_{mem_id}",
            "noop"
        ),
        parse_mode="Markdown"
    )


async def search_del_yes(update: Update, context):
    query = update.callback_query
    await query.answer()
    parts    = query.data.split("_")
    mem_type = parts[3]
    mem_id   = int(parts[4])
    conn = get_conn()
    conn.execute("DELETE FROM memories WHERE id=?", (mem_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text(
        "🗑️ Memory deleted. It has also been removed from your history list."
    )
