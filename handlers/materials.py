"""
Materials Handler
materials_home → [📚 Books] [📐 Formulas]
Books: Class → Subject → Book name (inline, 1 per row) → Send PDF
Formulas: existing formula_home flow
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
)
from database import get_conn
from ui import back_btn, E
from handlers.common import check_banned
import logging

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
#  MATERIALS HOME — Books | Formulas
# ════════════════════════════════════════════════════════════════════════════
async def materials_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END

    kb = Markup([
        [Btn("📚 Books",    callback_data="books_class"),
         Btn("📐 Formulas", callback_data="formula_home")],
        [Btn(f"{E['back']} Back", callback_data="home")],
    ])
    await query.edit_message_text(
        "📚 *Materials*\n\nChoose what you need:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BOOKS — Step 1: Class
# ════════════════════════════════════════════════════════════════════════════
async def books_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END

    kb = Markup([
        [Btn("📗 Class 11", callback_data="books_subj_11"),
         Btn("📘 Class 12", callback_data="books_subj_12")],
        [Btn(f"{E['back']} Back", callback_data="materials_home")],
    ])
    await query.edit_message_text(
        "📚 *Books*\n\nSelect class:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BOOKS — Step 2: Subject (from DB, only subjects that have books)
# ════════════════════════════════════════════════════════════════════════════
async def books_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_num = query.data.split("_")[2]   # "11" or "12"

    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT subject FROM books WHERE class_num=? ORDER BY subject",
        (class_num,)
    ).fetchall()
    conn.close()

    if not rows:
        await query.edit_message_text(
            f"No books uploaded for Class {class_num} yet.",
            reply_markup=back_btn("books_class")
        )
        return ConversationHandler.END

    subjects = [r["subject"] for r in rows]
    kb_rows = []
    # 2 per row
    for i in range(0, len(subjects), 2):
        row = [Btn(subjects[i], callback_data=f"books_list_{class_num}_{subjects[i]}")]
        if i + 1 < len(subjects):
            row.append(Btn(subjects[i+1], callback_data=f"books_list_{class_num}_{subjects[i+1]}"))
        kb_rows.append(row)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="books_class")])

    label = "📗 Class 11" if class_num == "11" else "📘 Class 12"
    await query.edit_message_text(
        f"{label} — Select subject:",
        reply_markup=Markup(kb_rows)
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BOOKS — Step 3: Book list (1 per row, full name visible)
# ════════════════════════════════════════════════════════════════════════════
async def books_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # pattern: books_list_11_PHY
    parts     = query.data.split("_", 3)
    class_num = parts[2]
    subject   = parts[3]

    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM books WHERE class_num=? AND subject=? ORDER BY book_name",
        (class_num, subject)
    ).fetchall()
    conn.close()

    if not rows:
        await query.edit_message_text(
            f"No books uploaded for {subject} — Class {class_num} yet. Contact Admin ( @carelessxowner ) to add books.",
            reply_markup=back_btn(f"books_subj_{class_num}")
        )
        return ConversationHandler.END

    # One button per row so full book name is visible
    kb_rows = [[Btn(f"📖 {r['book_name']}", callback_data=f"books_open_{r['id']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"books_subj_{class_num}")])

    await query.edit_message_text(
        f"📚 Class {class_num} — *{subject}*\n\nSelect a book:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BOOKS — Step 4: Send the PDF
# ════════════════════════════════════════════════════════════════════════════
async def books_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    book_id = int(query.data.split("_")[2])

    conn = get_conn()
    book = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    conn.close()

    if not book:
        await query.edit_message_text(
            "Book not found.",
            reply_markup=back_btn("books_class")
        )
        return ConversationHandler.END

    await query.edit_message_text(
        f"📖 Sending *{book['book_name']}*...",
        reply_markup=back_btn(f"books_list_{book['class_num']}_{book['subject']}"),
        parse_mode="Markdown"
    )

    try:
        await context.bot.send_document(
            update.effective_user.id,
            document=book["file_id"],
            caption=f"📖 *{book['book_name']}*\nClass {book['class_num']} | {book['subject']}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Book send error: {e}")
        await context.bot.send_message(
            update.effective_user.id,
            "❌ Could not send the book file. Please contact admin."
        )

    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_materials_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(materials_home, pattern="^materials_home$"),
            CallbackQueryHandler(books_class,    pattern="^books_class$"),
            CallbackQueryHandler(books_subject,  pattern=r"^books_subj_(11|12)$"),
            CallbackQueryHandler(books_list,     pattern=r"^books_list_(11|12)_.+$"),
            CallbackQueryHandler(books_open,     pattern=r"^books_open_\d+$"),
        ],
        states={},
        fallbacks=[
            CallbackQueryHandler(materials_home, pattern="^materials_home$"),
            CommandHandler("start", materials_home),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
