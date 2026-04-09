from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
)
from database import get_conn, get_sections
from ui import back_btn, E
from handlers.common import check_banned
import logging

logger = logging.getLogger(__name__)

PAGE_SIZE   = 8
EXAM_LABELS = {
    "mains": "📝 JEE Mains",
    "adv":   "🔬 JEE Advanced",
    "neet":  "🩺 NEET",
}


# ════════════════════════════════════════════════════════════════════════════
#  MATERIALS HOME — dynamic from DB
# ════════════════════════════════════════════════════════════════════════════
async def materials_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return ConversationHandler.END

    sections = get_sections()
    kb_rows  = []
    row      = []
    for sec in sections:
        label = f"{sec['emoji']} {sec['name']}"
        cb    = _section_entry_cb(sec)
        row.append(Btn(label, callback_data=cb))
        if len(row) == 2:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="home")])

    await query.edit_message_text(
        "📚 *Materials*\n\nChoose what you need:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


def _section_entry_cb(sec: dict) -> str:
    """Return the right callback_data for a section based on its type."""
    st  = sec["section_type"]
    sid = sec["id"]
    if   st == "formula": return "formula_home"
    elif st == "books":   return f"sec_books_class_{sid}"
    elif st == "mix":     return f"sec_mix_home_{sid}"
    elif st == "pyq":     return f"sec_pyq_home_{sid}"
    return "materials_home"


# ════════════════════════════════════════════════════════════════════════════
#  BOOKS SECTION — sec_books_class_{sid}
#  Class → Subject → Book list (paginated) → PDF(s)
# ════════════════════════════════════════════════════════════════════════════
async def sec_books_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    await query.answer()
    parts     = query.data.split("_")   # sec_books_class_{sid}
    sid       = int(parts[3])
    _store_sid(context, sid)

    conn = get_conn()
    sec  = conn.execute("SELECT * FROM material_sections WHERE id=?", (sid,)).fetchone()
    # Get all classes that have books in this section (or legacy null)
    classes = conn.execute(
        """SELECT DISTINCT class_num FROM books
           WHERE (section_id=? OR section_id IS NULL) AND class_num IS NOT NULL
           ORDER BY class_num""",
        (sid,)
    ).fetchall()
    conn.close()

    sec_name = sec["name"] if sec else "Books"
    # Build class buttons dynamically — works for 11, 12, or any custom class
    class_list = [r["class_num"] for r in classes]
    class_icons = {"11": "📗", "12": "📘"}

    kb_rows = []
    row     = []
    for cls in class_list:
        icon  = class_icons.get(cls, "📁")
        row.append(Btn(f"{icon} Class {cls}", callback_data=f"sec_books_subj_{sid}_{cls}"))
        if len(row) == 2:
            kb_rows.append(row); row = []
    if row:
        kb_rows.append(row)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="materials_home")])

    if not class_list:
        await query.edit_message_text(
            f"📚 *{sec_name}*\n\nNo books uploaded yet.",
            reply_markup=Markup(kb_rows), parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            f"📚 *{sec_name}*\n\nSelect class:",
            reply_markup=Markup(kb_rows), parse_mode="Markdown"
        )
    return ConversationHandler.END


async def sec_books_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    await query.answer()
    # sec_books_subj_{sid}_{class_num}
    parts     = query.data.split("_", 4)
    sid       = int(parts[3])
    class_num = parts[4]

    conn = get_conn()
    rows = conn.execute(
        """SELECT DISTINCT subject FROM books
           WHERE (section_id=? OR section_id IS NULL) AND class_num=? AND subject IS NOT NULL
           ORDER BY subject""",
        (sid, class_num)
    ).fetchall()
    conn.close()

    subjects  = [r["subject"] for r in rows]
    kb_rows   = []
    row       = []
    for s in subjects:
        row.append(Btn(s, callback_data=f"sec_books_list_{sid}_{class_num}_{s}_p1"))
        if len(row) == 2:
            kb_rows.append(row); row = []
    if row:
        kb_rows.append(row)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"sec_books_class_{sid}")])

    if not subjects:
        await query.edit_message_text(
            f"No subjects found for Class {class_num}.",
            reply_markup=Markup(kb_rows)
        )
    else:
        await query.edit_message_text(
            f"Class {class_num} — Select subject:",
            reply_markup=Markup(kb_rows)
        )
    return ConversationHandler.END


async def sec_books_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # sec_books_list_{sid}_{class_num}_{subject}_p{page}
    raw   = query.data
    parts = raw.split("_", 5)
    sid       = int(parts[3])
    class_num = parts[4]
    rest      = parts[5]   # "PHY_p1"
    if "_p" in rest:
        subject, pg_str = rest.rsplit("_p", 1)
        page = int(pg_str)
    else:
        subject = rest; page = 1

    conn = get_conn()
    rows = conn.execute(
        """SELECT DISTINCT book_name FROM books
           WHERE (section_id=? OR section_id IS NULL) AND class_num=? AND subject=?
           ORDER BY book_name""",
        (sid, class_num, subject)
    ).fetchall()
    conn.close()

    total = len(rows)
    if not total:
        await query.edit_message_text(
            f"No books found for {subject} — Class {class_num}.",
            reply_markup=back_btn(f"sec_books_subj_{sid}_{class_num}")
        )
        return ConversationHandler.END

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page        = max(1, min(page, total_pages))
    page_rows   = rows[(page-1)*PAGE_SIZE : page*PAGE_SIZE]

    kb_rows = [
        [Btn(f"📖 {r['book_name']}", callback_data=f"sec_books_open_{sid}_{class_num}_{subject}_{r['book_name']}")]
        for r in page_rows
    ]
    nav = _nav_row(page, total_pages, f"sec_books_list_{sid}_{class_num}_{subject}_p")
    if nav: kb_rows.append(nav)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"sec_books_subj_{sid}_{class_num}")])

    await query.edit_message_text(
        f"📚 Class {class_num} — *{subject}*\n_{total} books, page {page}/{total_pages}_\n\nSelect a book:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def sec_books_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # sec_books_open_{sid}_{class_num}_{subject}_{book_name}
    parts     = query.data.split("_", 6)
    sid       = int(parts[3])
    class_num = parts[4]
    subject   = parts[5]
    book_name = parts[6]

    conn  = get_conn()
    files = conn.execute(
        """SELECT * FROM books
           WHERE (section_id=? OR section_id IS NULL) AND class_num=? AND subject=? AND book_name=?
           ORDER BY id""",
        (sid, class_num, subject, book_name)
    ).fetchall()
    conn.close()

    await query.edit_message_text(
        f"📖 Sending *{book_name}*...",
        reply_markup=back_btn(f"sec_books_list_{sid}_{class_num}_{subject}_p1"),
        parse_mode="Markdown"
    )
    for f in files:
        try:
            await context.bot.send_document(
                update.effective_user.id,
                document=f["file_id"],
                caption=f"📖 *{book_name}*\nClass {class_num} | {subject}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Book send error: {e}")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  MIX SECTION — sec_mix_home_{sid}
#  Direct book list (no class) → PDF(s)
# ════════════════════════════════════════════════════════════════════════════
async def sec_mix_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sid   = int(query.data.split("_")[3])
    # pagination: sec_mix_home_{sid}_p{page}
    raw   = query.data
    page  = 1
    if "_p" in raw.split("_")[-1] if raw.count("_") >= 4 else "":
        page = int(raw.split("_p")[-1])

    conn = get_conn()
    sec  = conn.execute("SELECT * FROM material_sections WHERE id=?", (sid,)).fetchone()
    rows = conn.execute(
        """SELECT book_name, COUNT(*) as cnt FROM mix_books
           WHERE section_id=? OR section_id IS NULL
           GROUP BY book_name ORDER BY book_name""",
        (sid,)
    ).fetchall()
    conn.close()

    sec_name = sec["name"] if sec else "Mix Books"
    total    = len(rows)

    if not total:
        await query.edit_message_text(
            f"🔀 *{sec_name}*\n\nNo books uploaded yet.",
            reply_markup=back_btn("materials_home"), parse_mode="Markdown"
        )
        return ConversationHandler.END

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page        = max(1, min(page, total_pages))
    page_rows   = rows[(page-1)*PAGE_SIZE : page*PAGE_SIZE]

    kb_rows = [
        [Btn(f"📗 {r['book_name']}  ({r['cnt']} file{'s' if r['cnt']>1 else ''})",
             callback_data=f"sec_mix_open_{sid}_{r['book_name']}")]
        for r in page_rows
    ]
    nav = _nav_row(page, total_pages, f"sec_mix_home_{sid}_p")
    if nav: kb_rows.append(nav)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="materials_home")])

    await query.edit_message_text(
        f"🔀 *{sec_name}*\n_{total} books, page {page}/{total_pages}_\n\nSelect a book:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def sec_mix_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # sec_mix_open_{sid}_{book_name}
    parts     = query.data.split("_", 4)
    sid       = int(parts[3])
    book_name = parts[4]

    conn  = get_conn()
    files = conn.execute(
        """SELECT * FROM mix_books
           WHERE (section_id=? OR section_id IS NULL) AND book_name=?
           ORDER BY id""",
        (sid, book_name)
    ).fetchall()
    conn.close()

    await query.edit_message_text(
        f"📗 Sending *{book_name}*...",
        reply_markup=back_btn(f"sec_mix_home_{sid}"),
        parse_mode="Markdown"
    )
    for f in files:
        try:
            await context.bot.send_document(
                update.effective_user.id,
                document=f["file_id"],
                caption=f"📗 *{book_name}*",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Mix send error: {e}")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  PYQ SECTION — sec_pyq_home_{sid}
#  ExamType → Title list (paginated) → PDFs
# ════════════════════════════════════════════════════════════════════════════
async def sec_pyq_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sid = int(query.data.split("_")[3])

    conn = get_conn()
    sec  = conn.execute("SELECT * FROM material_sections WHERE id=?", (sid,)).fetchone()
    conn.close()
    sec_name = sec["name"] if sec else "PYQs"

    kb = Markup([
        [Btn("📝 JEE Mains",    callback_data=f"sec_pyq_list_{sid}_mains_p1"),
         Btn("🔬 JEE Advanced", callback_data=f"sec_pyq_list_{sid}_adv_p1")],
        [Btn("🩺 NEET",          callback_data=f"sec_pyq_list_{sid}_neet_p1")],
        [Btn(f"{E['back']} Back", callback_data="materials_home")],
    ])
    await query.edit_message_text(
        f"📋 *{sec_name}*\n\nSelect exam type:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


async def sec_pyq_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # sec_pyq_list_{sid}_{exam_type}_p{page}
    raw   = query.data
    parts = raw.split("_")
    sid       = int(parts[3])
    exam_type = parts[4]
    page      = int(parts[5].replace("p","")) if len(parts) > 5 else 1

    conn = get_conn()
    rows = conn.execute(
        """SELECT title, COUNT(*) as cnt FROM pyqs
           WHERE (section_id=? OR section_id IS NULL) AND exam_type=?
           GROUP BY title ORDER BY title""",
        (sid, exam_type)
    ).fetchall()
    conn.close()

    label = EXAM_LABELS.get(exam_type, exam_type)
    total = len(rows)
    if not total:
        await query.edit_message_text(
            f"No PYQs for {label} yet.",
            reply_markup=back_btn(f"sec_pyq_home_{sid}")
        )
        return ConversationHandler.END

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page        = max(1, min(page, total_pages))
    page_rows   = rows[(page-1)*PAGE_SIZE : page*PAGE_SIZE]

    kb_rows = [
        [Btn(f"📄 {r['title']}  ({r['cnt']} file{'s' if r['cnt']>1 else ''})",
             callback_data=f"sec_pyq_open_{sid}_{exam_type}_{r['title']}")]
        for r in page_rows
    ]
    nav = _nav_row(page, total_pages, f"sec_pyq_list_{sid}_{exam_type}_p")
    if nav: kb_rows.append(nav)
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"sec_pyq_home_{sid}")])

    await query.edit_message_text(
        f"📋 *{label}*\n_{total} papers, page {page}/{total_pages}_\n\nSelect paper:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def sec_pyq_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # sec_pyq_open_{sid}_{exam_type}_{title}
    parts     = query.data.split("_", 5)
    sid       = int(parts[3])
    exam_type = parts[4]
    title     = parts[5]

    conn  = get_conn()
    files = conn.execute(
        """SELECT * FROM pyqs
           WHERE (section_id=? OR section_id IS NULL) AND exam_type=? AND title=?
           ORDER BY id""",
        (sid, exam_type, title)
    ).fetchall()
    conn.close()

    label = EXAM_LABELS.get(exam_type, exam_type)
    await query.edit_message_text(
        f"📋 *{title}*\n{label}\n\nSending {len(files)} file(s)...",
        reply_markup=back_btn(f"sec_pyq_list_{sid}_{exam_type}_p1"),
        parse_mode="Markdown"
    )
    for f in files:
        try:
            await context.bot.send_document(
                update.effective_user.id,
                document=f["file_id"],
                caption=f"📄 *{f['file_name'] or title}*\n{label}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"PYQ send error: {e}")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  LEGACY ROUTES (old callbacks still work — backward compat)
# ════════════════════════════════════════════════════════════════════════════
async def books_class(update, context):
    """Legacy: books_class → find first 'books' section and redirect."""
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    sec  = conn.execute("SELECT id FROM material_sections WHERE section_type='books' ORDER BY id LIMIT 1").fetchone()
    conn.close()
    sid = sec["id"] if sec else 1
    query.data = f"sec_books_class_{sid}"
    return await sec_books_class(update, context)

async def mix_home(update, context):
    """Legacy: mix_home → find first 'mix' section."""
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    sec  = conn.execute("SELECT id FROM material_sections WHERE section_type='mix' ORDER BY id LIMIT 1").fetchone()
    conn.close()
    sid = sec["id"] if sec else 4
    query.data = f"sec_mix_home_{sid}"
    return await sec_mix_home(update, context)

async def pyq_home(update, context):
    """Legacy: pyq_home → find first 'pyq' section."""
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    sec  = conn.execute("SELECT id FROM material_sections WHERE section_type='pyq' ORDER BY id LIMIT 1").fetchone()
    conn.close()
    sid = sec["id"] if sec else 3
    query.data = f"sec_pyq_home_{sid}"
    return await sec_pyq_home(update, context)


# ════════════════════════════════════════════════════════════════════════════
#  HELPER
# ════════════════════════════════════════════════════════════════════════════
def _nav_row(page: int, total_pages: int, prefix: str):
    if total_pages <= 1:
        return None
    row = []
    if page > 1:
        row.append(Btn("⬅️ Prev", callback_data=f"{prefix}{page-1}"))
    row.append(Btn(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        row.append(Btn("Next ➡️", callback_data=f"{prefix}{page+1}"))
    return row

def _store_sid(context, sid):
    context.user_data["current_sid"] = sid


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_materials_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(materials_home,   pattern="^materials_home$"),
            # Dynamic section entry points
            CallbackQueryHandler(sec_books_class,  pattern=r"^sec_books_class_\d+$"),
            CallbackQueryHandler(sec_books_subj,   pattern=r"^sec_books_subj_\d+_.+$"),
            CallbackQueryHandler(sec_books_list,   pattern=r"^sec_books_list_\d+_.+$"),
            CallbackQueryHandler(sec_books_open,   pattern=r"^sec_books_open_\d+_.+$"),
            CallbackQueryHandler(sec_mix_home,     pattern=r"^sec_mix_home_\d+"),
            CallbackQueryHandler(sec_mix_open,     pattern=r"^sec_mix_open_\d+_.+$"),
            CallbackQueryHandler(sec_pyq_home,     pattern=r"^sec_pyq_home_\d+$"),
            CallbackQueryHandler(sec_pyq_list,     pattern=r"^sec_pyq_list_\d+_(mains|adv|neet)_p\d+$"),
            CallbackQueryHandler(sec_pyq_open,     pattern=r"^sec_pyq_open_\d+_(mains|adv|neet)_.+$"),
            # Legacy routes (backward compat)
            CallbackQueryHandler(books_class,      pattern="^books_class$"),
            CallbackQueryHandler(mix_home,         pattern="^mix_home$"),
            CallbackQueryHandler(pyq_home,         pattern="^pyq_home$"),
        ],
        states={},
        fallbacks=[
            CallbackQueryHandler(materials_home, pattern="^materials_home$"),
            CommandHandler("start", materials_home),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
