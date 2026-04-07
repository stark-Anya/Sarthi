"""
Formula Handler
Navigation: Formula Home → Class (11/12) → Subject → Chapter → Send files
"""
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
    kb = Markup([
        [Btn("📗 Class 11", callback_data="fclass_11"),
         Btn("📘 Class 12", callback_data="fclass_12")],
        [Btn(f"{E['back']} Back", callback_data="home")],
    ])
    await query.edit_message_text(
        f"{E['formulas']} *Formula Library*\n\nSelect class:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


async def formula_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_num = query.data.split("_")[1]
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT subject FROM formulas WHERE class_num=? AND subject IS NOT NULL ORDER BY subject",
        (class_num,)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text(
            f"No formulas uploaded for Class {class_num} yet.",
            reply_markup=back_btn("formula_home")
        )
        return ConversationHandler.END
    subjects = [r["subject"] for r in rows]
    kb_rows = []
    for i in range(0, len(subjects), 2):
        row = [Btn(subjects[i], callback_data=f"fsubj_{class_num}_{subjects[i]}")]
        if i + 1 < len(subjects):
            row.append(Btn(subjects[i+1], callback_data=f"fsubj_{class_num}_{subjects[i+1]}"))
        kb_rows.append(row)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="formula_home")])
    label = "📗 Class 11" if class_num == "11" else "📘 Class 12"
    await query.edit_message_text(
        f"{label} — Select subject:",
        reply_markup=Markup(kb_rows)
    )
    return ConversationHandler.END


async def formula_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 2)
    class_num = parts[1]
    subject   = parts[2]
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT chapter FROM formulas WHERE class_num=? AND subject=? ORDER BY chapter",
        (class_num, subject)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text(
            f"No chapters found for {subject} — Class {class_num}.",
            reply_markup=back_btn(f"fclass_{class_num}")
        )
        return ConversationHandler.END
    chapters = [r["chapter"] for r in rows]
    kb_rows = []
    for i in range(0, len(chapters), 2):
        row = [Btn(chapters[i], callback_data=f"fchap_{class_num}_{subject}_{chapters[i]}")]
        if i + 1 < len(chapters):
            row.append(Btn(chapters[i+1], callback_data=f"fchap_{class_num}_{subject}_{chapters[i+1]}"))
        kb_rows.append(row)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"fclass_{class_num}")])
    await query.edit_message_text(
        f"📚 Class {class_num} — *{subject}*\n\nSelect chapter:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def formula_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 3)
    class_num = parts[1]
    subject   = parts[2]
    chapter   = parts[3]
    conn = get_conn()
    entries = conn.execute(
        "SELECT * FROM formulas WHERE class_num=? AND subject=? AND chapter=? ORDER BY id",
        (class_num, subject, chapter)
    ).fetchall()
    conn.close()
    if not entries:
        await query.edit_message_text(
            f"No formulas found for *{chapter}*.",
            reply_markup=back_btn(f"fsubj_{class_num}_{subject}"),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    await query.edit_message_text(
        f"📐 *{chapter}* — Class {class_num} | {subject}\n\nSending {len(entries)} formula(s)...",
        reply_markup=back_btn(f"fsubj_{class_num}_{subject}"),
        parse_mode="Markdown"
    )
    for entry in entries:
        try:
            caption = f"📐 *{chapter}*\n{entry['content'] or ''}"
            if entry["file_id"] and entry["file_type"] == "photo":
                await context.bot.send_photo(update.effective_user.id, photo=entry["file_id"],
                    caption=caption, parse_mode="Markdown")
            elif entry["file_id"] and entry["file_type"] == "document":
                await context.bot.send_document(update.effective_user.id, document=entry["file_id"],
                    caption=caption, parse_mode="Markdown")
            elif entry["content"]:
                await context.bot.send_message(update.effective_user.id,
                    f"📐 *{chapter}* — Class {class_num} | {subject}\n\n{entry['content']}",
                    parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Formula send error: {e}")
    return ConversationHandler.END


def build_formula_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(formula_home,    pattern="^formula_home$"),
            CallbackQueryHandler(formula_class,   pattern=r"^fclass_(11|12)$"),
            CallbackQueryHandler(formula_subject, pattern=r"^fsubj_(11|12)_.+$"),
            CallbackQueryHandler(formula_chapter, pattern=r"^fchap_(11|12)_.+_.+$"),
        ],
        states={},
        fallbacks=[
            CallbackQueryHandler(formula_home, pattern="^formula_home$"),
            CommandHandler("start", formula_home),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
