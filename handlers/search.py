from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import ContextTypes
from database import get_conn
from handlers.common import check_banned
import logging

logger = logging.getLogger(__name__)


def _uid(update: Update):
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE tg_id=?",
                       (update.effective_user.id,)).fetchone()
    conn.close()
    return row["id"] if row else None


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return
    if not context.args:
        await update.message.reply_text(
            "🔍 Usage: `/search <query>`\n\nExample: `/search integration`",
            parse_mode="Markdown"
        )
        return

    query = " ".join(context.args).strip().lower()
    uid = _uid(update)
    conn = get_conn()

    # Search memories
    memories = conn.execute(
        """SELECT * FROM memories
           WHERE user_id=? AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)
           ORDER BY created DESC LIMIT 10""",
        (uid, f"%{query}%", f"%{query}%")
    ).fetchall()

    # Search daily reports
    reports = conn.execute(
        """SELECT * FROM daily_reports
           WHERE user_id=? AND (LOWER(date) LIKE ? OR LOWER(content) LIKE ?)
           ORDER BY date DESC LIMIT 5""",
        (uid, f"%{query}%", f"%{query}%")
    ).fetchall()

    # Search formulas by chapter
    formulas = conn.execute(
        """SELECT DISTINCT class_num, chapter FROM formulas
           WHERE LOWER(chapter) LIKE ?
           ORDER BY class_num, chapter LIMIT 10""",
        (f"%{query}%",)
    ).fetchall()

    conn.close()

    has_results = memories or reports or formulas
    if not has_results:
        await update.message.reply_text(f"🔍 No results found for *{query}*.", parse_mode="Markdown")
        return

    await update.message.reply_text(
        f"🔍 *Search results for:* `{query}`",
        parse_mode="Markdown"
    )

    # Send memory results
    if memories:
        await update.message.reply_text(f"🧠 *Memories ({len(memories)}):*", parse_mode="Markdown")
        for m in memories:
            label_map = {"silly": "🤪", "error": "❗", "important": "⭐"}
            emoji = label_map.get(m["mem_type"], "📌")
            text = f"{emoji} *{m['title']}*\n{m['created'][:10]}\n{(m['content'] or '')[:200]}"
            kb = None
            if m["mem_type"] in ("error", "important") and (m["answer"] or m["keypoints"]):
                kb = Markup([[Btn("📖 Answer & Key Points", callback_data=f"mem_ans_{m['mem_type']}_0")]])
            if m["file_id"] and m["file_type"] == "photo":
                await context.bot.send_photo(
                    update.effective_user.id,
                    photo=m["file_id"],
                    caption=text,
                    reply_markup=kb,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")

    # Send report results
    if reports:
        await update.message.reply_text(f"📒 *Daily Reports ({len(reports)}):*", parse_mode="Markdown")
        for r in reports:
            text = f"📒 *{r['date']}*\n{(r['content'] or '')[:300]}"
            if r["file_id"] and r["file_type"] == "photo":
                await context.bot.send_photo(
                    update.effective_user.id,
                    photo=r["file_id"],
                    caption=text,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(text, parse_mode="Markdown")

    # Send formula chapter buttons
    if formulas:
        rows = [[Btn(f"📐 Class {f['class_num']}: {f['chapter']}",
                     callback_data=f"formula_ch_{f['class_num']}_{f['chapter']}")] for f in formulas]
        await update.message.reply_text(
            f"📐 *Formula Chapters ({len(formulas)}):*",
            reply_markup=Markup(rows),
            parse_mode="Markdown"
        )
