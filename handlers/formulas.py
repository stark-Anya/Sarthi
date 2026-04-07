from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn
from ui import back_btn, E
from handlers.common import check_banned
import logging

logger = logging.getLogger(__name__)


async def formula_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END

    conn = get_conn()
    rows_11 = conn.execute(
        "SELECT DISTINCT chapter FROM formulas WHERE class_num='11' ORDER BY chapter"
    ).fetchall()
    rows_12 = conn.execute(
        "SELECT DISTINCT chapter FROM formulas WHERE class_num='12' ORDER BY chapter"
    ).fetchall()
    conn.close()

    kb_rows = []
    if rows_11:
        kb_rows.append([Btn("━━ Class 11 ━━", callback_data="noop")])
        chapters_11 = [r["chapter"] for r in rows_11]
        for i in range(0, len(chapters_11), 2):
            row = [Btn(chapters_11[i], callback_data=f"formula_ch_11_{chapters_11[i]}")]
            if i + 1 < len(chapters_11):
                row.append(Btn(chapters_11[i + 1], callback_data=f"formula_ch_11_{chapters_11[i + 1]}"))
            kb_rows.append(row)

    if rows_12:
        kb_rows.append([Btn("━━ Class 12 ━━", callback_data="noop")])
        chapters_12 = [r["chapter"] for r in rows_12]
        for i in range(0, len(chapters_12), 2):
            row = [Btn(chapters_12[i], callback_data=f"formula_ch_12_{chapters_12[i]}")]
            if i + 1 < len(chapters_12):
                row.append(Btn(chapters_12[i + 1], callback_data=f"formula_ch_12_{chapters_12[i + 1]}"))
            kb_rows.append(row)

    if not rows_11 and not rows_12:
        kb_rows.append([Btn("No formulas yet. Ask admin to add!", callback_data="noop")])

    kb_rows.append([Btn(f"{E['back']} Back", callback_data="home")])
    await query.edit_message_text(
        f"{E['formulas']} *Formulas Library*\n\nSelect a chapter:",
        reply_markup=Markup(kb_rows),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def formula_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # pattern: formula_ch_11_Waves
    parts = query.data.split("_", 3)
    class_num = parts[2]
    chapter = parts[3]

    conn = get_conn()
    entries = conn.execute(
        "SELECT * FROM formulas WHERE class_num=? AND chapter=? ORDER BY id",
        (class_num, chapter)
    ).fetchall()
    conn.close()

    if not entries:
        await query.edit_message_text(
            f"No formulas found for *{chapter}*.",
            reply_markup=back_btn("formula_home"),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await query.edit_message_text(
        f"📐 *{chapter}* — Sending {len(entries)} formula(s)...",
        reply_markup=back_btn("formula_home"),
        parse_mode="Markdown"
    )

    for entry in entries:
        try:
            if entry["file_id"] and entry["file_type"] == "photo":
                await context.bot.send_photo(
                    update.effective_user.id,
                    photo=entry["file_id"],
                    caption=entry["content"] or chapter,
                    parse_mode="Markdown"
                )
            elif entry["file_id"] and entry["file_type"] == "document":
                await context.bot.send_document(
                    update.effective_user.id,
                    document=entry["file_id"],
                    caption=entry["content"] or chapter
                )
            elif entry["content"]:
                await context.bot.send_message(
                    update.effective_user.id,
                    f"📐 *{chapter}*\n\n{entry['content']}",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Formula send error: {e}")

    return ConversationHandler.END


def build_formula_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(formula_home,    pattern="^formula_home$"),
            CallbackQueryHandler(formula_chapter, pattern=r"^formula_ch_(11|12)_.+$"),
        ],
        states={},
        fallbacks=[
            CallbackQueryHandler(formula_home, pattern="^formula_home$"),
            CommandHandler("start", formula_home),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
