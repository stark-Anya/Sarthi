"""
Materials Handler
materials_home → Books | Formulas | PYQs | 11&12 Mix

Books   : Class → Subject → Book list (1/row) → Send PDF
Formulas: formula_home (existing)
PYQs    : JEE Mains | JEE Adv | NEET → Title list → Send all PDFs
Mix     : Direct book list (no class) → Send PDF(s)
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

EXAM_LABELS = {
    "mains": "📝 JEE Mains",
    "adv":   "🔬 JEE Advanced",
    "neet":  "🩺 NEET",
}


# ════════════════════════════════════════════════════════════════════════════
#  MATERIALS HOME — 4 sections
# ════════════════════════════════════════════════════════════════════════════
async def materials_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END
    kb = Markup([
        [Btn("📚 Books",       callback_data="books_class"),
         Btn("📐 Formulas",    callback_data="formula_home")],
        [Btn("📋 PYQs",        callback_data="pyq_home"),
         Btn("🔀 11&12 Mix",   callback_data="mix_home")],
        [Btn(f"{E['back']} Back", callback_data="home")],
    ])
    await query.edit_message_text(
        "📚 *Materials*\n\nChoose what you need:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BOOKS — Class → Subject → Book list → PDF
# ════════════════════════════════════════════════════════════════════════════
async def books_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📗 Class 11", callback_data="books_subj_11"),
         Btn("📘 Class 12", callback_data="books_subj_12")],
        [Btn(f"{E['back']} Back", callback_data="materials_home")],
    ])
    await query.edit_message_text("📚 *Books*\n\nSelect class:", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def books_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_num = query.data.split("_")[2]
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT subject FROM books WHERE class_num=? ORDER BY subject", (class_num,)
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
    for i in range(0, len(subjects), 2):
        row = [Btn(subjects[i], callback_data=f"books_list_{class_num}_{subjects[i]}")]
        if i + 1 < len(subjects):
            row.append(Btn(subjects[i+1], callback_data=f"books_list_{class_num}_{subjects[i+1]}"))
        kb_rows.append(row)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="books_class")])
    label = "📗 Class 11" if class_num == "11" else "📘 Class 12"
    await query.edit_message_text(f"{label} — Select subject:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def books_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
            f"No books uploaded for {subject} — Class {class_num} yet.",
            reply_markup=back_btn(f"books_subj_{class_num}")
        )
        return ConversationHandler.END
    kb_rows = [[Btn(f"📖 {r['book_name']}", callback_data=f"books_open_{r['id']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"books_subj_{class_num}")])
    await query.edit_message_text(
        f"📚 Class {class_num} — *{subject}*\n\nSelect a book:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def books_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    book_id = int(query.data.split("_")[2])
    conn = get_conn()
    book = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    conn.close()
    if not book:
        await query.edit_message_text("Book not found.", reply_markup=back_btn("books_class"))
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
        await context.bot.send_message(update.effective_user.id, "❌ Could not send book. Contact admin.")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  PYQs — JEE Mains | JEE Adv | NEET → Title list → Send all PDFs
# ════════════════════════════════════════════════════════════════════════════
async def pyq_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END
    kb = Markup([
        [Btn("📝 JEE Mains",    callback_data="pyq_list_mains"),
         Btn("🔬 JEE Advanced", callback_data="pyq_list_adv")],
        [Btn("🩺 NEET",          callback_data="pyq_list_neet")],
        [Btn(f"{E['back']} Back", callback_data="materials_home")],
    ])
    await query.edit_message_text(
        "📋 *Previous Year Questions*\n\nSelect exam:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


async def pyq_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all titles for a given exam type."""
    query = update.callback_query
    await query.answer()
    exam_type = query.data.split("_")[2]   # mains / adv / neet
    conn = get_conn()
    # Get distinct titles with file count
    rows = conn.execute(
        """SELECT title, COUNT(*) as cnt
           FROM pyqs WHERE exam_type=?
           GROUP BY title ORDER BY title""",
        (exam_type,)
    ).fetchall()
    conn.close()
    label = EXAM_LABELS.get(exam_type, exam_type)
    if not rows:
        await query.edit_message_text(
            f"No PYQs uploaded for {label} yet.",
            reply_markup=back_btn("pyq_home")
        )
        return ConversationHandler.END
    kb_rows = [
        [Btn(f"📄 {r['title']}  ({r['cnt']} file{'s' if r['cnt']>1 else ''})",
             callback_data=f"pyq_open_{exam_type}_{r['title']}")]
        for r in rows
    ]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="pyq_home")])
    await query.edit_message_text(
        f"📋 *{label}*\n\nSelect a paper:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def pyq_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send all PDFs for a given exam_type + title."""
    query = update.callback_query
    await query.answer()
    # pattern: pyq_open_mains_JEE Mains 2023
    parts     = query.data.split("_", 3)
    exam_type = parts[2]
    title     = parts[3]
    conn = get_conn()
    files = conn.execute(
        "SELECT * FROM pyqs WHERE exam_type=? AND title=? ORDER BY id",
        (exam_type, title)
    ).fetchall()
    conn.close()
    label = EXAM_LABELS.get(exam_type, exam_type)
    if not files:
        await query.edit_message_text("No files found.", reply_markup=back_btn(f"pyq_list_{exam_type}"))
        return ConversationHandler.END
    await query.edit_message_text(
        f"📋 *{title}*\n{label}\n\nSending {len(files)} file(s)...",
        reply_markup=back_btn(f"pyq_list_{exam_type}"), parse_mode="Markdown"
    )
    for f in files:
        try:
            fname = f["file_name"] or title
            await context.bot.send_document(
                update.effective_user.id,
                document=f["file_id"],
                caption=f"📄 *{fname}*\n{label}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"PYQ send error: {e}")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  11&12 MIX — Direct book list → PDF(s)
# ════════════════════════════════════════════════════════════════════════════
async def mix_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END
    conn = get_conn()
    # Each book_name may have multiple files — group them
    rows = conn.execute(
        """SELECT book_name, COUNT(*) as cnt
           FROM mix_books GROUP BY book_name ORDER BY book_name"""
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text(
            "No mix books uploaded yet.",
            reply_markup=back_btn("materials_home")
        )
        return ConversationHandler.END
    kb_rows = [
        [Btn(f"📗 {r['book_name']}  ({r['cnt']} file{'s' if r['cnt']>1 else ''})",
             callback_data=f"mix_open_{r['book_name']}")]
        for r in rows
    ]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="materials_home")])
    await query.edit_message_text(
        "🔀 *11 & 12 Mix Books*\n\nSelect a book:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def mix_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # pattern: mix_open_Book Name Here
    book_name = query.data.split("_", 2)[2]
    conn = get_conn()
    files = conn.execute(
        "SELECT * FROM mix_books WHERE book_name=? ORDER BY id", (book_name,)
    ).fetchall()
    conn.close()
    if not files:
        await query.edit_message_text("No files found.", reply_markup=back_btn("mix_home"))
        return ConversationHandler.END
    await query.edit_message_text(
        f"📗 *{book_name}*\n\nSending {len(files)} file(s)...",
        reply_markup=back_btn("mix_home"), parse_mode="Markdown"
    )
    for f in files:
        try:
            fname = f["file_name"] or book_name
            await context.bot.send_document(
                update.effective_user.id,
                document=f["file_id"],
                caption=f"📗 *{fname}*",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Mix book send error: {e}")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_materials_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(materials_home,  pattern="^materials_home$"),
            # Books
            CallbackQueryHandler(books_class,     pattern="^books_class$"),
            CallbackQueryHandler(books_subject,   pattern=r"^books_subj_(11|12)$"),
            CallbackQueryHandler(books_list,      pattern=r"^books_list_(11|12)_.+$"),
            CallbackQueryHandler(books_open,      pattern=r"^books_open_\d+$"),
            # PYQs
            CallbackQueryHandler(pyq_home,        pattern="^pyq_home$"),
            CallbackQueryHandler(pyq_list,        pattern=r"^pyq_list_(mains|adv|neet)$"),
            CallbackQueryHandler(pyq_open,        pattern=r"^pyq_open_(mains|adv|neet)_.+$"),
            # Mix
            CallbackQueryHandler(mix_home,        pattern="^mix_home$"),
            CallbackQueryHandler(mix_open,        pattern=r"^mix_open_.+$"),
        ],
        states={},
        fallbacks=[
            CallbackQueryHandler(materials_home, pattern="^materials_home$"),
            CommandHandler("start", materials_home),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
