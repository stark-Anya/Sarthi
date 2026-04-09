"""
Admin Panel
- Password-only auth (koi bhi password dal ke access kar sakta hai — no ADMIN_ID check)
- Formulas: Upload + Delete
- Books: Upload + Delete (multiple PDFs per book supported)
- PYQs: Upload + Delete (exam_type + title + multiple PDFs)
- Mix Books: Upload + Delete (no class, just name + multiple PDFs)
- Broadcast, Stats, Manage Users, Clear Database
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn, get_all_users, get_sections, add_section, delete_section
from ui import back_btn, cancel_btn, subject_kb, confirm_delete_kb, E
from config import ADMIN_PASS, DB_CLEAR_PASS
import logging

logger = logging.getLogger(__name__)

# ── States ───────────────────────────────────────────────────────────────────
(
    ADMIN_PASS_STATE,
    # Formula upload
    FORMULA_CLASS, FORMULA_CHAPTER, FORMULA_SUBJ, FORMULA_FILE,
    # Book upload
    BOOK_CLASS, BOOK_SUBJ, BOOK_NAME, BOOK_FILES,
    # PYQ upload
    PYQ_EXAM, PYQ_TITLE, PYQ_FILES,
    # Mix upload
    MIX_NAME, MIX_FILES,
    # Edit
    EDIT_VALUE,
    # Others
    BROADCAST_TEXT,
    DB_CLEAR_PASS_STATE,
    # Section management
    SEC_NAME, SEC_EMOJI,
) = range(19)

_authed: set = set()   # session-authed tg_ids (password-based, no ID check)


def _is_authed(tg_id: int) -> bool:
    return tg_id in _authed


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY / LOGIN  — password only, anyone can access
# ════════════════════════════════════════════════════════════════════════════
async def admin_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    if _is_authed(tg_id):
        return await _show_admin_panel(update, context)
    await query.edit_message_text(
        "🛡️ *Admin Login*\n\nEnter admin password:",
        reply_markup=cancel_btn("home"), parse_mode="Markdown"
    )
    return ADMIN_PASS_STATE


async def admin_got_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    if update.message.text.strip() == ADMIN_PASS:
        _authed.add(tg_id)
        await update.message.reply_text("✅ Authenticated! Welcome to Admin Panel.")
        return await _show_admin_panel_msg(update, context)
    else:
        await update.message.reply_text(
            "❌ Wrong password. Try again:",
            reply_markup=cancel_btn("home")
        )
        return ADMIN_PASS_STATE


def _admin_kb():
    return Markup([
        [Btn("📐 Formulas",        callback_data="admin_formula_menu"),
         Btn("📚 Books",           callback_data="admin_book_menu")],
        [Btn("📋 PYQs",            callback_data="admin_pyq_menu"),
         Btn("🔀 Mix Books",       callback_data="admin_mix_menu")],
        [Btn("🗂️ Manage Sections", callback_data="admin_sec_menu"),
         Btn("✏️ Edit Content",    callback_data="admin_edit_menu")],
        [Btn(f"{E['broadcast']} Broadcast", callback_data="admin_broadcast"),
         Btn(f"{E['stats']} Stats",         callback_data="admin_stats")],
        [Btn(f"{E['users']} Users",         callback_data="admin_users"),
         Btn("🗄️ Clear DB",                 callback_data="admin_cleardb")],
        [Btn(f"{E['back']} Back",           callback_data="home")],
    ])


async def _show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("🛡️ *Admin Panel*", reply_markup=_admin_kb(), parse_mode="Markdown")
    return ConversationHandler.END


async def _show_admin_panel_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ *Admin Panel*", reply_markup=_admin_kb(), parse_mode="Markdown")
    return ConversationHandler.END


async def admin_panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _is_authed(update.effective_user.id):
        await query.answer("Session expired. Please go back and login again.", show_alert=True)
        return ConversationHandler.END
    await query.edit_message_text("🛡️ *Admin Panel*", reply_markup=_admin_kb(), parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  FORMULAS — Upload + Delete
# ════════════════════════════════════════════════════════════════════════════
async def admin_formula_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("➕ Upload Formula",  callback_data="admin_formula_add"),
         Btn("🗑️ Delete Formula",  callback_data="admin_formula_del_class")],
        [Btn(f"{E['back']} Back",  callback_data="admin_panel_back")],
    ])
    await query.edit_message_text("📐 *Formula Management*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_formula_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("formula_draft", None)
    kb = Markup([
        [Btn("📗 Class 11", callback_data="afc_11"),
         Btn("📘 Class 12", callback_data="afc_12")],
        [Btn(f"{E['cancel']} Cancel", callback_data="admin_formula_menu")],
    ])
    await query.edit_message_text("➕ *Add Formula*\n\nSelect class:", reply_markup=kb, parse_mode="Markdown")
    return FORMULA_CLASS


async def afc_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["formula_draft"] = {"class_num": query.data.split("_")[1]}
    await query.edit_message_text("Enter chapter name:", reply_markup=cancel_btn("admin_formula_menu"))
    return FORMULA_CHAPTER


async def afc_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["formula_draft"]["chapter"] = update.message.text.strip()
    await update.message.reply_text("Select subject:", reply_markup=subject_kb("afs"))
    return FORMULA_SUBJ


async def afc_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["formula_draft"]["subject"] = query.data.replace("afs_", "")
    await query.edit_message_text(
        "Send the formula (PDF, image, or text):",
        reply_markup=cancel_btn("admin_formula_menu")
    )
    return FORMULA_FILE


async def afc_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("formula_draft", {})
    file_id = file_type = content = None
    if update.message.photo:
        file_id = update.message.photo[-1].file_id; file_type = "photo"; content = update.message.caption or ""
    elif update.message.document:
        file_id = update.message.document.file_id; file_type = "document"; content = update.message.caption or ""
    else:
        content = update.message.text.strip()
    conn = get_conn()
    conn.execute(
        "INSERT INTO formulas (class_num, chapter, subject, file_id, file_type, content, added_by) VALUES (?,?,?,?,?,?,?)",
        (d.get("class_num"), d.get("chapter"), d.get("subject"), file_id, file_type, content, update.effective_user.id)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Formula added to *{d.get('chapter')}* — Class {d.get('class_num')} | {d.get('subject')}",
        reply_markup=Markup([
            [Btn("➕ Add Another", callback_data="admin_formula_add"),
             Btn(f"{E['back']} Back", callback_data="admin_formula_menu")]
        ]), parse_mode="Markdown"
    )
    return ConversationHandler.END


# Formula Delete
async def admin_formula_del_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📗 Class 11", callback_data="afdel_class_11"),
         Btn("📘 Class 12", callback_data="afdel_class_12")],
        [Btn(f"{E['back']} Back", callback_data="admin_formula_menu")],
    ])
    await query.edit_message_text("🗑️ *Delete Formula*\n\nSelect class:", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_formula_del_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_num = query.data.split("_")[2]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT subject FROM formulas WHERE class_num=? ORDER BY subject", (class_num,)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No formulas for this class.", reply_markup=back_btn("admin_formula_del_class"))
        return ConversationHandler.END
    subjects = [r["subject"] for r in rows if r["subject"]]
    kb_rows = [[Btn(s, callback_data=f"afdel_subj_{class_num}_{s}")] for s in subjects]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="admin_formula_del_class")])
    await query.edit_message_text(f"Class {class_num} — Select subject:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def admin_formula_del_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 3); class_num = parts[2]; subject = parts[3]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT chapter FROM formulas WHERE class_num=? AND subject=? ORDER BY chapter", (class_num, subject)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No chapters found.", reply_markup=back_btn(f"afdel_class_{class_num}"))
        return ConversationHandler.END
    chapters = [r["chapter"] for r in rows]
    kb_rows = [[Btn(c, callback_data=f"afdel_entries_{class_num}_{subject}_{c}")] for c in chapters]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"afdel_class_{class_num}")])
    await query.edit_message_text(f"Class {class_num} — {subject}\nSelect chapter:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def admin_formula_del_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 4); class_num = parts[2]; subject = parts[3]; chapter = parts[4]
    conn = get_conn()
    rows = conn.execute("SELECT * FROM formulas WHERE class_num=? AND subject=? AND chapter=? ORDER BY id", (class_num, subject, chapter)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No entries found.", reply_markup=back_btn(f"afdel_subj_{class_num}_{subject}"))
        return ConversationHandler.END
    kb_rows = []
    for r in rows:
        label = (r["content"] or "")[:30] or (r["file_type"] or "file")
        kb_rows.append([Btn(f"🗑️ {label}", callback_data=f"afdel_confirm_{r['id']}")])
    kb_rows.append([Btn("🗑️ Delete ALL in this chapter", callback_data=f"afdel_all_confirm_{class_num}_{subject}_{chapter}")])
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"afdel_subj_{class_num}_{subject}")])
    await query.edit_message_text(f"*{chapter}* — {len(rows)} entries\nSelect to delete:", reply_markup=Markup(kb_rows), parse_mode="Markdown")
    return ConversationHandler.END


async def admin_formula_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fid = int(query.data.split("_")[-1])
    conn = get_conn()
    row = conn.execute("SELECT * FROM formulas WHERE id=?", (fid,)).fetchone()
    conn.close()
    if not row:
        await query.answer("Not found.", show_alert=True); return ConversationHandler.END
    await query.edit_message_text(
        f"⚠️ Delete formula entry?\n*{row['chapter']}* — {(row['content'] or row['file_type'] or '')[:50]}",
        reply_markup=confirm_delete_kb(f"afdel_yes_{fid}", "admin_formula_menu"), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_formula_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fid = int(query.data.split("_")[-1])
    conn = get_conn()
    conn.execute("DELETE FROM formulas WHERE id=?", (fid,))
    conn.commit(); conn.close()
    await query.edit_message_text("🗑️ Formula entry deleted.", reply_markup=back_btn("admin_formula_menu"))
    return ConversationHandler.END


async def admin_formula_del_all_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 4); class_num = parts[3]; rest = parts[4].split("_", 1)
    subject = rest[0]; chapter = rest[1] if len(rest) > 1 else ""
    context.user_data["del_all"] = {"class_num": class_num, "subject": subject, "chapter": chapter}
    await query.edit_message_text(
        f"⚠️ *Cannot be undone!*\nDelete ALL formulas for:\nClass {class_num} | {subject} | *{chapter}*?",
        reply_markup=confirm_delete_kb("afdel_all_yes", "admin_formula_menu"), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_formula_del_all_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("del_all", {})
    conn = get_conn()
    conn.execute("DELETE FROM formulas WHERE class_num=? AND subject=? AND chapter=?",
                 (d.get("class_num"), d.get("subject"), d.get("chapter")))
    conn.commit(); conn.close()
    await query.edit_message_text("🗑️ Chapter deleted.", reply_markup=back_btn("admin_formula_menu"))
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BOOKS — Upload (multiple PDFs) + Delete
# ════════════════════════════════════════════════════════════════════════════
async def admin_book_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("➕ Upload Book",  callback_data="admin_book_add"),
         Btn("🗑️ Delete Book", callback_data="admin_book_del_class")],
        [Btn(f"{E['back']} Back", callback_data="admin_panel_back")],
    ])
    await query.edit_message_text("📚 *Book Management*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_book_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("book_draft", None)
    # Show available 'books' type sections to pick from
    sections = [s for s in get_sections() if s["section_type"] == "books"]
    if not sections:
        # fallback — no section, use None
        context.user_data["book_draft"] = {"section_id": None}
        kb = Markup([
            [Btn("📗 Class 11", callback_data="abk_class_11"),
             Btn("📘 Class 12", callback_data="abk_class_12")],
            [Btn(f"{E['cancel']} Cancel", callback_data="admin_book_menu")],
        ])
        await query.edit_message_text("📚 *Upload Book*\n\nSelect class:", reply_markup=kb, parse_mode="Markdown")
        return BOOK_CLASS

    if len(sections) == 1:
        # Only one section — skip selection
        context.user_data["book_draft"] = {"section_id": sections[0]["id"]}
        kb = Markup([
            [Btn("📗 Class 11", callback_data="abk_class_11"),
             Btn("📘 Class 12", callback_data="abk_class_12")],
            [Btn("📁 Custom class", callback_data="abk_class_custom")],
            [Btn(f"{E['cancel']} Cancel", callback_data="admin_book_menu")],
        ])
        await query.edit_message_text(
            f"📚 *Upload Book* → {sections[0]['emoji']} {sections[0]['name']}\n\nSelect class:",
            reply_markup=kb, parse_mode="Markdown"
        )
        return BOOK_CLASS

    # Multiple sections — let admin pick
    kb_rows = [
        [Btn(f"{s['emoji']} {s['name']}", callback_data=f"abk_sec_{s['id']}")]
        for s in sections
    ]
    kb_rows.append([Btn(f"{E['cancel']} Cancel", callback_data="admin_book_menu")])
    await query.edit_message_text(
        "📚 *Upload Book*\n\nWhich section?",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return BOOK_CLASS


async def abk_sec_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin picked which books section to upload to."""
    query = update.callback_query
    await query.answer()
    sid = int(query.data.split("_")[2])
    context.user_data["book_draft"] = {"section_id": sid}
    kb = Markup([
        [Btn("📗 Class 11", callback_data="abk_class_11"),
         Btn("📘 Class 12", callback_data="abk_class_12")],
        [Btn("📁 Custom class", callback_data="abk_class_custom")],
        [Btn(f"{E['cancel']} Cancel", callback_data="admin_book_menu")],
    ])
    await query.edit_message_text("Select class:", reply_markup=kb)
    return BOOK_CLASS


async def abk_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    val = query.data.split("_")[2]
    if val == "custom":
        context.user_data.setdefault("book_draft", {})["class_num"] = "__custom__"
        await query.edit_message_text(
            "Enter class name (e.g. `11`, `12`, `13`, `Dropper`):",
            reply_markup=cancel_btn("admin_book_menu"), parse_mode="Markdown"
        )
        return BOOK_NAME   # reuse state — handle in abk_name_or_class below
    context.user_data.setdefault("book_draft", {})["class_num"] = val
    await query.edit_message_text("Select subject:", reply_markup=subject_kb("abks"))
    return BOOK_SUBJ


async def abk_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["book_draft"]["subject"] = query.data.replace("abks_", "")
    await query.edit_message_text(
        "Enter the *book name* (e.g. `HC Verma Vol 1`):",
        reply_markup=cancel_btn("admin_book_menu"), parse_mode="Markdown"
    )
    return BOOK_NAME


async def abk_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["book_draft"]["book_name"] = update.message.text.strip()
    d = context.user_data["book_draft"]
    context.user_data["book_draft"]["count"] = 0
    await update.message.reply_text(
        f"📤 Now send PDF files one by one for:\n\n"
        f"📖 *{d['book_name']}* — Class {d['class_num']} | {d['subject']}\n\n"
        f"Send as many PDFs as you want. When done, tap *Done* button.",
        reply_markup=Markup([[Btn("✅ Done uploading", callback_data="abk_done")]]),
        parse_mode="Markdown"
    )
    return BOOK_FILES


async def abk_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("book_draft", {})
    if not update.message.document:
        await update.message.reply_text(
            "❌ Please send a PDF file (document).",
            reply_markup=Markup([[Btn("✅ Done uploading", callback_data="abk_done")]])
        )
        return BOOK_FILES
    file_id   = update.message.document.file_id
    conn = get_conn()
    conn.execute(
        "INSERT INTO books (section_id, class_num, subject, book_name, file_id, added_by) VALUES (?,?,?,?,?,?)",
        (d.get("section_id"), d.get("class_num"), d.get("subject"), d.get("book_name"),
         file_id, update.effective_user.id)
    )
    conn.commit(); conn.close()
    count = d.get("count", 0) + 1
    context.user_data["book_draft"]["count"] = count
    await update.message.reply_text(
        f"✅ File {count} uploaded! Send more or tap Done.",
        reply_markup=Markup([[Btn("✅ Done uploading", callback_data="abk_done")]])
    )
    return BOOK_FILES


async def abk_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("book_draft", {})
    count = d.get("count", 0)
    if count == 0:
        await query.edit_message_text(
            "⚠️ No files uploaded yet. Send at least one PDF.",
            reply_markup=Markup([[Btn(f"{E['cancel']} Cancel", callback_data="admin_book_menu")]])
        )
        return BOOK_FILES
    await query.edit_message_text(
        f"✅ *{d.get('book_name')}* saved!\n{count} file(s) uploaded.\nClass {d.get('class_num')} | {d.get('subject')}",
        reply_markup=Markup([
            [Btn("➕ Upload Another", callback_data="admin_book_add"),
             Btn(f"{E['back']} Back", callback_data="admin_book_menu")]
        ]), parse_mode="Markdown"
    )
    return ConversationHandler.END


# Book Delete
async def admin_book_del_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📗 Class 11", callback_data="abkdel_class_11"),
         Btn("📘 Class 12", callback_data="abkdel_class_12")],
        [Btn(f"{E['back']} Back", callback_data="admin_book_menu")],
    ])
    await query.edit_message_text("🗑️ *Delete Book*\n\nSelect class:", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_book_del_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_num = query.data.split("_")[2]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT subject FROM books WHERE class_num=? ORDER BY subject", (class_num,)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text(f"No books for Class {class_num}.", reply_markup=back_btn("admin_book_del_class"))
        return ConversationHandler.END
    subjects = [r["subject"] for r in rows]
    kb_rows = [[Btn(s, callback_data=f"abkdel_subj_{class_num}_{s}")] for s in subjects]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="admin_book_del_class")])
    await query.edit_message_text(f"Class {class_num} — Select subject:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def admin_book_del_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 3); class_num = parts[2]; subject = parts[3]
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT book_name FROM books WHERE class_num=? AND subject=? ORDER BY book_name", (class_num, subject)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No books found.", reply_markup=back_btn(f"abkdel_class_{class_num}"))
        return ConversationHandler.END
    kb_rows = [[Btn(f"🗑️ {r['book_name']}", callback_data=f"abkdel_confirm_{class_num}_{subject}_{r['book_name']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"abkdel_class_{class_num}")])
    await query.edit_message_text(f"Class {class_num} | {subject}\nSelect book to delete:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def admin_book_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # pattern: abkdel_confirm_11_PHY_HC Verma
    parts = query.data.split("_", 4); class_num = parts[2]; subject = parts[3]; book_name = parts[4]
    context.user_data["del_book"] = {"class_num": class_num, "subject": subject, "book_name": book_name}
    await query.edit_message_text(
        f"⚠️ Delete book *{book_name}*?\nClass {class_num} | {subject}\n(All files will be deleted)",
        reply_markup=confirm_delete_kb("abkdel_yes", "admin_book_menu"), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_book_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("del_book", {})
    conn = get_conn()
    conn.execute("DELETE FROM books WHERE class_num=? AND subject=? AND book_name=?",
                 (d.get("class_num"), d.get("subject"), d.get("book_name")))
    conn.commit(); conn.close()
    await query.edit_message_text("🗑️ Book deleted.", reply_markup=back_btn("admin_book_menu"))
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  PYQs — Upload (exam_type + title + multiple PDFs) + Delete
# ════════════════════════════════════════════════════════════════════════════
async def admin_pyq_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("➕ Upload PYQ",  callback_data="admin_pyq_add"),
         Btn("🗑️ Delete PYQ", callback_data="admin_pyq_del_exam")],
        [Btn(f"{E['back']} Back", callback_data="admin_panel_back")],
    ])
    await query.edit_message_text("📋 *PYQ Management*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_pyq_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("pyq_draft", None)
    kb = Markup([
        [Btn("📝 JEE Mains",    callback_data="apyq_exam_mains"),
         Btn("🔬 JEE Advanced", callback_data="apyq_exam_adv")],
        [Btn("🩺 NEET",          callback_data="apyq_exam_neet")],
        [Btn(f"{E['cancel']} Cancel", callback_data="admin_pyq_menu")],
    ])
    await query.edit_message_text("📋 *Upload PYQ*\n\nSelect exam type:", reply_markup=kb, parse_mode="Markdown")
    return PYQ_EXAM


async def apyq_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exam_type = query.data.replace("apyq_exam_", "")
    context.user_data["pyq_draft"] = {"exam_type": exam_type, "count": 0}
    exam_labels = {"mains": "JEE Mains", "adv": "JEE Advanced", "neet": "NEET"}
    await query.edit_message_text(
        f"📋 *{exam_labels.get(exam_type, exam_type)}*\n\n"
        f"Enter a title for this paper\n(e.g. `JEE Mains 2024 Jan`, `NEET 2023`):",
        reply_markup=cancel_btn("admin_pyq_menu"), parse_mode="Markdown"
    )
    return PYQ_TITLE


async def apyq_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pyq_draft"]["title"] = update.message.text.strip()
    d = context.user_data["pyq_draft"]
    exam_labels = {"mains": "JEE Mains", "adv": "JEE Advanced", "neet": "NEET"}
    await update.message.reply_text(
        f"📤 Now send PDF files one by one for:\n\n"
        f"📋 *{d['title']}* — {exam_labels.get(d['exam_type'], '')}\n\n"
        f"Send as many PDFs as you want. Tap *Done* when finished.",
        reply_markup=Markup([[Btn("✅ Done uploading", callback_data="apyq_done")]]),
        parse_mode="Markdown"
    )
    return PYQ_FILES


async def apyq_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("pyq_draft", {})
    if not update.message.document:
        await update.message.reply_text(
            "❌ Please send a PDF file (document).",
            reply_markup=Markup([[Btn("✅ Done uploading", callback_data="apyq_done")]])
        )
        return PYQ_FILES
    file_id   = update.message.document.file_id
    file_name = update.message.document.file_name or d.get("title", "")
    conn = get_conn()
    conn.execute(
        "INSERT INTO pyqs (section_id, exam_type, title, file_id, file_name, added_by) VALUES (?,?,?,?,?,?)",
        (d.get("section_id"), d.get("exam_type"), d.get("title"),
         file_id, file_name, update.effective_user.id)
    )
    conn.commit(); conn.close()
    count = d.get("count", 0) + 1
    context.user_data["pyq_draft"]["count"] = count
    await update.message.reply_text(
        f"✅ File {count} uploaded! Send more or tap Done.",
        reply_markup=Markup([[Btn("✅ Done uploading", callback_data="apyq_done")]])
    )
    return PYQ_FILES


async def apyq_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("pyq_draft", {})
    count = d.get("count", 0)
    if count == 0:
        await query.edit_message_text(
            "⚠️ No files uploaded yet. Send at least one PDF.",
            reply_markup=Markup([[Btn(f"{E['cancel']} Cancel", callback_data="admin_pyq_menu")]])
        )
        return PYQ_FILES
    exam_labels = {"mains": "JEE Mains", "adv": "JEE Advanced", "neet": "NEET"}
    await query.edit_message_text(
        f"✅ *{d.get('title')}* saved!\n{count} file(s) uploaded.\n{exam_labels.get(d.get('exam_type',''), '')}",
        reply_markup=Markup([
            [Btn("➕ Upload Another", callback_data="admin_pyq_add"),
             Btn(f"{E['back']} Back", callback_data="admin_pyq_menu")]
        ]), parse_mode="Markdown"
    )
    return ConversationHandler.END


# PYQ Delete
async def admin_pyq_del_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📝 JEE Mains",    callback_data="apyqdel_exam_mains"),
         Btn("🔬 JEE Advanced", callback_data="apyqdel_exam_adv")],
        [Btn("🩺 NEET",          callback_data="apyqdel_exam_neet")],
        [Btn(f"{E['back']} Back", callback_data="admin_pyq_menu")],
    ])
    await query.edit_message_text("🗑️ *Delete PYQ*\n\nSelect exam:", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_pyq_del_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exam_type = query.data.replace("apyqdel_exam_", "")
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT title FROM pyqs WHERE exam_type=? ORDER BY title", (exam_type,)
    ).fetchall()
    conn.close()
    exam_labels = {"mains": "JEE Mains", "adv": "JEE Advanced", "neet": "NEET"}
    if not rows:
        await query.edit_message_text(
            f"No PYQs for {exam_labels.get(exam_type, '')}.", reply_markup=back_btn("admin_pyq_del_exam")
        )
        return ConversationHandler.END
    kb_rows = [[Btn(f"🗑️ {r['title']}", callback_data=f"apyqdel_confirm_{exam_type}_{r['title']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="admin_pyq_del_exam")])
    await query.edit_message_text(
        f"{exam_labels.get(exam_type, '')} — Select paper to delete:",
        reply_markup=Markup(kb_rows)
    )
    return ConversationHandler.END


async def admin_pyq_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 3); exam_type = parts[2]; title = parts[3]
    context.user_data["del_pyq"] = {"exam_type": exam_type, "title": title}
    conn = get_conn()
    cnt = conn.execute("SELECT COUNT(*) FROM pyqs WHERE exam_type=? AND title=?", (exam_type, title)).fetchone()[0]
    conn.close()
    exam_labels = {"mains": "JEE Mains", "adv": "JEE Advanced", "neet": "NEET"}
    await query.edit_message_text(
        f"⚠️ Delete *{title}*?\n{exam_labels.get(exam_type, '')} — {cnt} file(s)\n(Cannot be undone)",
        reply_markup=confirm_delete_kb("apyqdel_yes", "admin_pyq_menu"), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_pyq_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("del_pyq", {})
    conn = get_conn()
    conn.execute("DELETE FROM pyqs WHERE exam_type=? AND title=?", (d.get("exam_type"), d.get("title")))
    conn.commit(); conn.close()
    await query.edit_message_text("🗑️ PYQ deleted.", reply_markup=back_btn("admin_pyq_menu"))
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  MIX BOOKS — Upload (name + multiple PDFs) + Delete
# ════════════════════════════════════════════════════════════════════════════
async def admin_mix_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("➕ Upload Mix Book",  callback_data="admin_mix_add"),
         Btn("🗑️ Delete Mix Book", callback_data="admin_mix_del_list")],
        [Btn(f"{E['back']} Back",   callback_data="admin_panel_back")],
    ])
    await query.edit_message_text("🔀 *11 & 12 Mix Books Management*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_mix_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("mix_draft", None)
    await query.edit_message_text(
        "🔀 *Upload Mix Book*\n\nEnter book name:",
        reply_markup=cancel_btn("admin_mix_menu"), parse_mode="Markdown"
    )
    return MIX_NAME


async def amix_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mix_draft"] = {"book_name": update.message.text.strip(), "count": 0}
    d = context.user_data["mix_draft"]
    await update.message.reply_text(
        f"📤 Send PDF files one by one for:\n📗 *{d['book_name']}*\n\nTap *Done* when finished.",
        reply_markup=Markup([[Btn("✅ Done uploading", callback_data="amix_done")]]),
        parse_mode="Markdown"
    )
    return MIX_FILES


async def amix_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("mix_draft", {})
    if not update.message.document:
        await update.message.reply_text(
            "❌ Please send a PDF file (document).",
            reply_markup=Markup([[Btn("✅ Done uploading", callback_data="amix_done")]])
        )
        return MIX_FILES
    file_id   = update.message.document.file_id
    file_name = update.message.document.file_name or d.get("book_name", "")
    conn = get_conn()
    conn.execute(
        "INSERT INTO mix_books (section_id, book_name, file_id, file_name, added_by) VALUES (?,?,?,?,?)",
        (d.get("section_id"), d.get("book_name"), file_id, file_name, update.effective_user.id)
    )
    conn.commit(); conn.close()
    count = d.get("count", 0) + 1
    context.user_data["mix_draft"]["count"] = count
    await update.message.reply_text(
        f"✅ File {count} uploaded! Send more or tap Done.",
        reply_markup=Markup([[Btn("✅ Done uploading", callback_data="amix_done")]])
    )
    return MIX_FILES


async def amix_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("mix_draft", {})
    count = d.get("count", 0)
    if count == 0:
        await query.edit_message_text(
            "⚠️ No files uploaded. Send at least one PDF.",
            reply_markup=Markup([[Btn(f"{E['cancel']} Cancel", callback_data="admin_mix_menu")]])
        )
        return MIX_FILES
    await query.edit_message_text(
        f"✅ *{d.get('book_name')}* saved!\n{count} file(s) uploaded.",
        reply_markup=Markup([
            [Btn("➕ Upload Another", callback_data="admin_mix_add"),
             Btn(f"{E['back']} Back", callback_data="admin_mix_menu")]
        ]), parse_mode="Markdown"
    )
    return ConversationHandler.END


# Mix Delete
async def admin_mix_del_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT book_name FROM mix_books ORDER BY book_name"
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No mix books uploaded.", reply_markup=back_btn("admin_mix_menu"))
        return ConversationHandler.END
    kb_rows = [[Btn(f"🗑️ {r['book_name']}", callback_data=f"amixdel_confirm_{r['book_name']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="admin_mix_menu")])
    await query.edit_message_text("Select mix book to delete:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def admin_mix_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    book_name = query.data.split("_", 2)[2]
    context.user_data["del_mix"] = book_name
    conn = get_conn()
    cnt = conn.execute("SELECT COUNT(*) FROM mix_books WHERE book_name=?", (book_name,)).fetchone()[0]
    conn.close()
    await query.edit_message_text(
        f"⚠️ Delete *{book_name}*?\n{cnt} file(s) will be deleted.",
        reply_markup=confirm_delete_kb("amixdel_yes", "admin_mix_menu"), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_mix_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    book_name = context.user_data.get("del_mix", "")
    conn = get_conn()
    conn.execute("DELETE FROM mix_books WHERE book_name=?", (book_name,))
    conn.commit(); conn.close()
    await query.edit_message_text("🗑️ Mix book deleted.", reply_markup=back_btn("admin_mix_menu"))
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BROADCAST
# ════════════════════════════════════════════════════════════════════════════
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📢 *Broadcast*\n\nSend the message to broadcast to all users:",
        reply_markup=cancel_btn("admin_panel_back"), parse_mode="Markdown"
    )
    return BROADCAST_TEXT


async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text  = update.message.text.strip()
    users = get_all_users()
    sent = failed = 0
    for u in users:
        try:
            await context.bot.send_message(u["tg_id"], f"📢 *Broadcast*\n\n{text}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await update.message.reply_text(
        f"📢 Broadcast done!\n✅ Sent: {sent}\n❌ Failed: {failed}",
        reply_markup=back_btn("admin_panel_back")
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  STATS
# ════════════════════════════════════════════════════════════════════════════
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    banned      = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    memories    = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    formulas    = conn.execute("SELECT COUNT(*) FROM formulas").fetchone()[0]
    books       = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    pyqs        = conn.execute("SELECT COUNT(*) FROM pyqs").fetchone()[0]
    mix         = conn.execute("SELECT COUNT(*) FROM mix_books").fetchone()[0]
    tasks       = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    text = (
        f"📊 *Bot Stats*\n\n"
        f"👥 Total Users: {total_users} (🚫 {banned} banned)\n"
        f"🧠 Memories: {memories}\n"
        f"📐 Formulas: {formulas} files\n"
        f"📚 Books: {books} files\n"
        f"📋 PYQs: {pyqs} files\n"
        f"🔀 Mix Books: {mix} files\n"
        f"📝 Tasks: {tasks}"
    )
    await query.edit_message_text(text, reply_markup=back_btn("admin_panel_back"), parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  MANAGE USERS
# ════════════════════════════════════════════════════════════════════════════
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    users = conn.execute("SELECT * FROM users ORDER BY joined DESC LIMIT 20").fetchall()
    conn.close()
    rows = []
    for u in users:
        status = "BANNED" if u["is_banned"] else "active"
        action = "✅ Unban" if u["is_banned"] else "🚫 Ban"
        rows.append([
            Btn(f"{(u['name'] or 'Unknown')[:28]} ({status})", callback_data="noop"),
            Btn(action, callback_data=f"admin_toggle_{u['tg_id']}")
        ])
    rows.append([Btn(f"{E['back']} Back", callback_data="admin_panel_back")])
    await query.edit_message_text("👥 *User Management* (last 20)", reply_markup=Markup(rows), parse_mode="Markdown")
    return ConversationHandler.END


async def admin_toggle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target_id = int(query.data.split("_")[-1])
    conn = get_conn()
    row = conn.execute("SELECT is_banned FROM users WHERE tg_id=?", (target_id,)).fetchone()
    if row:
        new_ban = 0 if row["is_banned"] else 1
        conn.execute("UPDATE users SET is_banned=? WHERE tg_id=?", (new_ban, target_id))
        conn.commit()
        try:
            msg = "🚫 You have been banned." if new_ban else "✅ You have been unbanned!"
            await context.bot.send_message(target_id, msg)
        except Exception:
            pass
    conn.close()
    await admin_users(update, context)


# ════════════════════════════════════════════════════════════════════════════
#  EDIT CONTENT — Formula chapter/subject rename | Book name rename | PYQ title rename
# ════════════════════════════════════════════════════════════════════════════
async def admin_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit menu — choose what to edit."""
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📐 Edit Formula Chapter", callback_data="edit_fml_class")],
        [Btn("📚 Rename Book",           callback_data="edit_book_class")],
        [Btn("📋 Rename PYQ Title",      callback_data="edit_pyq_exam")],
        [Btn("🔀 Rename Mix Book",        callback_data="edit_mix_list")],
        [Btn(f"{E['back']} Back",        callback_data="admin_panel_back")],
    ])
    await query.edit_message_text("✏️ *Edit Content*\n\nSelect what to edit:", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


# ── Edit Formula Chapter name ─────────────────────────────────────────────
async def edit_fml_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📗 Class 11", callback_data="edit_fml_subj_11"),
         Btn("📘 Class 12", callback_data="edit_fml_subj_12")],
        [Btn(f"{E['back']} Back", callback_data="admin_edit_menu")],
    ])
    await query.edit_message_text("Select class:", reply_markup=kb)
    return ConversationHandler.END


async def edit_fml_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_num = query.data.split("_")[-1]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT subject FROM formulas WHERE class_num=? ORDER BY subject", (class_num,)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No formulas.", reply_markup=back_btn("admin_edit_menu"))
        return ConversationHandler.END
    kb_rows = [[Btn(r["subject"], callback_data=f"edit_fml_chap_{class_num}_{r['subject']}")] for r in rows if r["subject"]]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="edit_fml_class")])
    await query.edit_message_text(f"Class {class_num} — Select subject:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def edit_fml_chap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 4); class_num = parts[3]; subject = parts[4]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT chapter FROM formulas WHERE class_num=? AND subject=? ORDER BY chapter", (class_num, subject)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No chapters.", reply_markup=back_btn(f"edit_fml_subj_{class_num}"))
        return ConversationHandler.END
    kb_rows = [[Btn(r["chapter"], callback_data=f"edit_fml_pick_{class_num}_{subject}_{r['chapter']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"edit_fml_subj_{class_num}")])
    await query.edit_message_text(f"Class {class_num} | {subject}\nSelect chapter to rename:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def edit_fml_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 5); class_num = parts[3]; subject = parts[4]; chapter = parts[5]
    context.user_data["edit"] = {"type": "formula_chapter", "class_num": class_num, "subject": subject, "old": chapter}
    await query.edit_message_text(
        f"✏️ Renaming chapter:\n*{chapter}*\n\nEnter new chapter name:",
        reply_markup=cancel_btn("admin_edit_menu"), parse_mode="Markdown"
    )
    return EDIT_VALUE


# ── Edit Book name ────────────────────────────────────────────────────────
async def edit_book_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📗 Class 11", callback_data="edit_book_subj_11"),
         Btn("📘 Class 12", callback_data="edit_book_subj_12")],
        [Btn(f"{E['back']} Back", callback_data="admin_edit_menu")],
    ])
    await query.edit_message_text("Select class:", reply_markup=kb)
    return ConversationHandler.END


async def edit_book_subj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_num = query.data.split("_")[-1]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT subject FROM books WHERE class_num=? ORDER BY subject", (class_num,)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No books.", reply_markup=back_btn("admin_edit_menu"))
        return ConversationHandler.END
    kb_rows = [[Btn(r["subject"], callback_data=f"edit_book_list_{class_num}_{r['subject']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="edit_book_class")])
    await query.edit_message_text(f"Class {class_num} — Select subject:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def edit_book_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 4); class_num = parts[3]; subject = parts[4]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT book_name FROM books WHERE class_num=? AND subject=? ORDER BY book_name", (class_num, subject)).fetchall()
    conn.close()
    kb_rows = [[Btn(r["book_name"], callback_data=f"edit_book_pick_{class_num}_{subject}_{r['book_name']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"edit_book_subj_{class_num}")])
    await query.edit_message_text(f"Select book to rename:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def edit_book_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 5); class_num = parts[3]; subject = parts[4]; old_name = parts[5]
    context.user_data["edit"] = {"type": "book_name", "class_num": class_num, "subject": subject, "old": old_name}
    await query.edit_message_text(
        f"✏️ Renaming:\n*{old_name}*\n\nEnter new book name:",
        reply_markup=cancel_btn("admin_edit_menu"), parse_mode="Markdown"
    )
    return EDIT_VALUE


# ── Edit PYQ Title ────────────────────────────────────────────────────────
async def edit_pyq_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📝 JEE Mains",    callback_data="edit_pyq_list_mains"),
         Btn("🔬 JEE Advanced", callback_data="edit_pyq_list_adv")],
        [Btn("🩺 NEET",          callback_data="edit_pyq_list_neet")],
        [Btn(f"{E['back']} Back", callback_data="admin_edit_menu")],
    ])
    await query.edit_message_text("Select exam:", reply_markup=kb)
    return ConversationHandler.END


async def edit_pyq_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exam_type = query.data.split("_")[-1]
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT title FROM pyqs WHERE exam_type=? ORDER BY title", (exam_type,)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No PYQs.", reply_markup=back_btn("edit_pyq_exam"))
        return ConversationHandler.END
    kb_rows = [[Btn(r["title"], callback_data=f"edit_pyq_pick_{exam_type}_{r['title']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="edit_pyq_exam")])
    await query.edit_message_text("Select title to rename:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def edit_pyq_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 4); exam_type = parts[3]; old_title = parts[4]
    context.user_data["edit"] = {"type": "pyq_title", "exam_type": exam_type, "old": old_title}
    await query.edit_message_text(
        f"✏️ Renaming:\n*{old_title}*\n\nEnter new title:",
        reply_markup=cancel_btn("admin_edit_menu"), parse_mode="Markdown"
    )
    return EDIT_VALUE


# ── Edit Mix Book name ────────────────────────────────────────────────────
async def edit_mix_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT book_name FROM mix_books ORDER BY book_name").fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No mix books.", reply_markup=back_btn("admin_edit_menu"))
        return ConversationHandler.END
    kb_rows = [[Btn(r["book_name"], callback_data=f"edit_mix_pick_{r['book_name']}")] for r in rows]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="admin_edit_menu")])
    await query.edit_message_text("Select mix book to rename:", reply_markup=Markup(kb_rows))
    return ConversationHandler.END


async def edit_mix_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    old_name = query.data.split("_", 3)[3]
    context.user_data["edit"] = {"type": "mix_name", "old": old_name}
    await query.edit_message_text(
        f"✏️ Renaming:\n*{old_name}*\n\nEnter new name:",
        reply_markup=cancel_btn("admin_edit_menu"), parse_mode="Markdown"
    )
    return EDIT_VALUE


# ── Save edit ─────────────────────────────────────────────────────────────
async def edit_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_val = update.message.text.strip()
    info    = context.user_data.get("edit", {})
    etype   = info.get("type")
    conn    = get_conn()
    msg     = "✅ Updated!"

    if etype == "formula_chapter":
        conn.execute(
            "UPDATE formulas SET chapter=? WHERE class_num=? AND subject=? AND chapter=?",
            (new_val, info["class_num"], info["subject"], info["old"])
        )
        msg = f"✅ Chapter renamed:\n*{info['old']}* → *{new_val}*"
    elif etype == "book_name":
        conn.execute(
            "UPDATE books SET book_name=? WHERE class_num=? AND subject=? AND book_name=?",
            (new_val, info["class_num"], info["subject"], info["old"])
        )
        msg = f"✅ Book renamed:\n*{info['old']}* → *{new_val}*"
    elif etype == "pyq_title":
        conn.execute(
            "UPDATE pyqs SET title=? WHERE exam_type=? AND title=?",
            (new_val, info["exam_type"], info["old"])
        )
        msg = f"✅ PYQ title renamed:\n*{info['old']}* → *{new_val}*"
    elif etype == "mix_name":
        conn.execute(
            "UPDATE mix_books SET book_name=? WHERE book_name=?",
            (new_val, info["old"])
        )
        msg = f"✅ Mix book renamed:\n*{info['old']}* → *{new_val}*"

    conn.commit()
    conn.close()
    await update.message.reply_text(
        msg,
        reply_markup=Markup([
            [Btn("✏️ Edit More",    callback_data="admin_edit_menu"),
             Btn(f"{E['back']} Back", callback_data="admin_panel_back")]
        ]),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  SECTION MANAGEMENT — Add / Delete sections from Materials home
# ════════════════════════════════════════════════════════════════════════════
async def admin_sec_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sections = get_sections()
    text = "🗂️ *Manage Materials Sections*\n\n"
    for s in sections:
        text += f"{s['emoji']} *{s['name']}* — _{s['section_type']}_\n"
    text += "\nAdd a new section or delete an existing one."
    kb = Markup([
        [Btn("➕ Add Section",    callback_data="admin_sec_add_type"),
         Btn("🗑️ Delete Section", callback_data="admin_sec_del_list")],
        [Btn(f"{E['back']} Back", callback_data="admin_panel_back")],
    ])
    await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def admin_sec_add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1 — Pick section type."""
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("📚 Books (Class→Subject→Book)", callback_data="addsec_type_books")],
        [Btn("🔀 Mix (Direct list, no class)",  callback_data="addsec_type_mix")],
        [Btn("📋 PYQ (Mains/Adv/NEET)",        callback_data="addsec_type_pyq")],
        [Btn("📐 Formula (same as Formulas)",   callback_data="addsec_type_formula")],
        [Btn(f"{E['cancel']} Cancel",           callback_data="admin_sec_menu")],
    ])
    await query.edit_message_text(
        "➕ *Add Section*\n\nChoose section type:",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_sec_got_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2 — Got type, ask for name."""
    query = update.callback_query
    await query.answer()
    sec_type = query.data.replace("addsec_type_", "")
    context.user_data["new_sec"] = {"type": sec_type}
    type_labels = {
        "books":   "Books (Class→Subject→Book)",
        "mix":     "Mix (Direct list)",
        "pyq":     "PYQ (Mains/Adv/NEET)",
        "formula": "Formula",
    }
    await query.edit_message_text(
        f"📝 Section type: *{type_labels.get(sec_type, sec_type)}*\n\n"
        f"Enter section *name* (e.g. `Class 12+ Books`, `NEET Books`, `HC Verma`):",
        reply_markup=cancel_btn("admin_sec_menu"), parse_mode="Markdown"
    )
    return SEC_NAME


async def admin_sec_got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3 — Got name, ask for emoji."""
    context.user_data["new_sec"]["name"] = update.message.text.strip()
    await update.message.reply_text(
        "Now send an *emoji* for this section (e.g. `📗` `🧪` `🔥`):",
        reply_markup=cancel_btn("admin_sec_menu"), parse_mode="Markdown"
    )
    return SEC_EMOJI


async def admin_sec_got_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4 — Save section."""
    emoji = update.message.text.strip()
    d     = context.user_data.get("new_sec", {})
    sid   = add_section(d.get("name", "New Section"), emoji, d.get("type", "mix"))
    await update.message.reply_text(
        f"✅ Section *{emoji} {d.get('name')}* created!\n"
        f"It now appears in Materials. You can upload content to it from the relevant menu.",
        reply_markup=Markup([
            [Btn("🗂️ Sections",     callback_data="admin_sec_menu"),
             Btn(f"{E['back']} Back", callback_data="admin_panel_back")]
        ]),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_sec_del_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all sections to delete."""
    query = update.callback_query
    await query.answer()
    sections = get_sections()
    if not sections:
        await query.edit_message_text("No sections found.", reply_markup=back_btn("admin_sec_menu"))
        return ConversationHandler.END
    kb_rows = [
        [Btn(f"🗑️ {s['emoji']} {s['name']} ({s['section_type']})",
             callback_data=f"addsec_del_confirm_{s['id']}")]
        for s in sections
    ]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="admin_sec_menu")])
    await query.edit_message_text(
        "🗑️ *Delete Section*\n\n⚠️ Deleting a section also deletes ALL its content!",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_sec_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sid = int(query.data.split("_")[-1])
    conn = get_conn()
    sec  = conn.execute("SELECT * FROM material_sections WHERE id=?", (sid,)).fetchone()
    conn.close()
    if not sec:
        await query.answer("Not found.", show_alert=True)
        return ConversationHandler.END
    from ui import confirm_delete_kb
    await query.edit_message_text(
        f"⚠️ *Cannot be undone!*\nDelete section *{sec['emoji']} {sec['name']}*?\n"
        f"All books/files in this section will also be deleted.",
        reply_markup=confirm_delete_kb(f"addsec_del_yes_{sid}", "admin_sec_menu"),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_sec_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sid = int(query.data.split("_")[-1])
    delete_section(sid)
    await query.edit_message_text(
        "🗑️ Section deleted.",
        reply_markup=back_btn("admin_sec_menu")
    )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  CLEAR DATABASE
# ════════════════════════════════════════════════════════════════════════════
async def admin_cleardb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("👥 Clear User Data",  callback_data="cleardb_user"),
         Btn("💥 Clear Everything", callback_data="cleardb_all")],
        [Btn(f"{E['back']} Back",   callback_data="admin_panel_back")],
    ])
    await query.edit_message_text(
        "🗄️ *Clear Database*\n\n"
        "👥 *User Data* — Deletes tasks, memories, reports, scores etc.\n"
        "Formulas, books, PYQs, mix books kept.\n\n"
        "💥 *Everything* — Deletes ALL data.\n\n"
        "⚠️ Requires separate confirmation password.",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cleardb_user_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cleardb_type"] = "user"
    await query.edit_message_text(
        "🔐 Enter the *database clear password* to confirm:\n_(Different from admin password)_",
        reply_markup=cancel_btn("admin_cleardb"), parse_mode="Markdown"
    )
    return DB_CLEAR_PASS_STATE


async def cleardb_all_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cleardb_type"] = "all"
    await query.edit_message_text(
        "🔐 Enter the *database clear password* to confirm:\n_(Different from admin password)_",
        reply_markup=cancel_btn("admin_cleardb"), parse_mode="Markdown"
    )
    return DB_CLEAR_PASS_STATE


async def cleardb_got_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip() != DB_CLEAR_PASS:
        await update.message.reply_text("❌ Wrong password.", reply_markup=cancel_btn("admin_cleardb"))
        return DB_CLEAR_PASS_STATE
    cleardb_type = context.user_data.get("cleardb_type", "user")
    conn = get_conn()
    if cleardb_type == "user":
        for table in ["tasks", "memories", "daily_reports", "thoughts", "motivation",
                      "study_log", "test_scores", "revision_schedule", "doubts", "lectures"]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit(); conn.close()
        await update.message.reply_text(
            "✅ *User data cleared!*\nFormulas, books, PYQs, mix books intact.",
            reply_markup=back_btn("admin_panel_back"), parse_mode="Markdown"
        )
    else:
        for table in ["tasks", "memories", "daily_reports", "thoughts", "motivation",
                      "study_log", "test_scores", "revision_schedule", "doubts", "lectures",
                      "formulas", "books", "pyqs", "mix_books", "users"]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit(); conn.close()
        _authed.discard(update.effective_user.id)
        await update.message.reply_text(
            "💥 *Full database cleared!* Use /start to re-register.", parse_mode="Markdown"
        )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_admin_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_home,                    pattern="^admin_home$"),
            CallbackQueryHandler(admin_panel_cb,                pattern="^admin_panel_back$"),
            # Formulas
            CallbackQueryHandler(admin_formula_menu,            pattern="^admin_formula_menu$"),
            CallbackQueryHandler(admin_formula_add,             pattern="^admin_formula_add$"),
            CallbackQueryHandler(admin_formula_del_class,       pattern="^admin_formula_del_class$"),
            CallbackQueryHandler(admin_formula_del_subj,        pattern=r"^afdel_class_(11|12)$"),
            CallbackQueryHandler(admin_formula_del_chapter,     pattern=r"^afdel_subj_(11|12)_.+$"),
            CallbackQueryHandler(admin_formula_del_entries,     pattern=r"^afdel_entries_(11|12)_.+$"),
            CallbackQueryHandler(admin_formula_del_confirm,     pattern=r"^afdel_confirm_\d+$"),
            CallbackQueryHandler(admin_formula_del_yes,         pattern=r"^afdel_yes_\d+$"),
            CallbackQueryHandler(admin_formula_del_all_confirm, pattern=r"^afdel_all_confirm_.+$"),
            CallbackQueryHandler(admin_formula_del_all_yes,     pattern="^afdel_all_yes$"),
            # Section management
            CallbackQueryHandler(admin_sec_menu,          pattern="^admin_sec_menu$"),
            CallbackQueryHandler(admin_sec_add_type,      pattern="^admin_sec_add_type$"),
            CallbackQueryHandler(admin_sec_got_type,      pattern=r"^addsec_type_(books|mix|pyq|formula)$"),
            CallbackQueryHandler(admin_sec_del_list,      pattern="^admin_sec_del_list$"),
            CallbackQueryHandler(admin_sec_del_confirm,   pattern=r"^addsec_del_confirm_\d+$"),
            CallbackQueryHandler(admin_sec_del_yes,       pattern=r"^addsec_del_yes_\d+$"),
            # Books — section pick
            CallbackQueryHandler(abk_sec_pick,            pattern=r"^abk_sec_\d+$"),
            CallbackQueryHandler(admin_book_add,                pattern="^admin_book_add$"),
            CallbackQueryHandler(abk_done,                      pattern="^abk_done$"),
            CallbackQueryHandler(admin_book_del_class,          pattern="^admin_book_del_class$"),
            CallbackQueryHandler(admin_book_del_subj,           pattern=r"^abkdel_class_(11|12)$"),
            CallbackQueryHandler(admin_book_del_list,           pattern=r"^abkdel_subj_(11|12)_.+$"),
            CallbackQueryHandler(admin_book_del_confirm,        pattern=r"^abkdel_confirm_(11|12)_.+$"),
            CallbackQueryHandler(admin_book_del_yes,            pattern="^abkdel_yes$"),
            # PYQs
            CallbackQueryHandler(admin_pyq_menu,                pattern="^admin_pyq_menu$"),
            CallbackQueryHandler(admin_pyq_add,                 pattern="^admin_pyq_add$"),
            CallbackQueryHandler(apyq_done,                     pattern="^apyq_done$"),
            CallbackQueryHandler(admin_pyq_del_exam,            pattern="^admin_pyq_del_exam$"),
            CallbackQueryHandler(admin_pyq_del_list,            pattern=r"^apyqdel_exam_(mains|adv|neet)$"),
            CallbackQueryHandler(admin_pyq_del_confirm,         pattern=r"^apyqdel_confirm_(mains|adv|neet)_.+$"),
            CallbackQueryHandler(admin_pyq_del_yes,             pattern="^apyqdel_yes$"),
            # Mix
            CallbackQueryHandler(admin_mix_menu,                pattern="^admin_mix_menu$"),
            CallbackQueryHandler(admin_mix_add,                 pattern="^admin_mix_add$"),
            CallbackQueryHandler(amix_done,                     pattern="^amix_done$"),
            CallbackQueryHandler(admin_mix_del_list,            pattern="^admin_mix_del_list$"),
            CallbackQueryHandler(admin_mix_del_confirm,         pattern=r"^amixdel_confirm_.+$"),
            CallbackQueryHandler(admin_mix_del_yes,             pattern="^amixdel_yes$"),
            # Others
            CallbackQueryHandler(admin_broadcast_start,         pattern="^admin_broadcast$"),
            CallbackQueryHandler(admin_stats,                   pattern="^admin_stats$"),
            CallbackQueryHandler(admin_users,                   pattern="^admin_users$"),
            CallbackQueryHandler(admin_toggle_ban,              pattern=r"^admin_toggle_\d+$"),
            CallbackQueryHandler(admin_cleardb,                 pattern="^admin_cleardb$"),
            CallbackQueryHandler(cleardb_user_ask,              pattern="^cleardb_user$"),
            CallbackQueryHandler(cleardb_all_ask,               pattern="^cleardb_all$"),
            # Edit
            CallbackQueryHandler(admin_edit_menu,               pattern="^admin_edit_menu$"),
            CallbackQueryHandler(edit_fml_class,                pattern="^edit_fml_class$"),
            CallbackQueryHandler(edit_fml_subj,                 pattern=r"^edit_fml_subj_(11|12)$"),
            CallbackQueryHandler(edit_fml_chap,                 pattern=r"^edit_fml_chap_(11|12)_.+$"),
            CallbackQueryHandler(edit_fml_pick,                 pattern=r"^edit_fml_pick_(11|12)_.+$"),
            CallbackQueryHandler(edit_book_class,               pattern="^edit_book_class$"),
            CallbackQueryHandler(edit_book_subj,                pattern=r"^edit_book_subj_(11|12)$"),
            CallbackQueryHandler(edit_book_list,                pattern=r"^edit_book_list_(11|12)_.+$"),
            CallbackQueryHandler(edit_book_pick,                pattern=r"^edit_book_pick_(11|12)_.+$"),
            CallbackQueryHandler(edit_pyq_exam,                 pattern="^edit_pyq_exam$"),
            CallbackQueryHandler(edit_pyq_list,                 pattern=r"^edit_pyq_list_(mains|adv|neet)$"),
            CallbackQueryHandler(edit_pyq_pick,                 pattern=r"^edit_pyq_pick_(mains|adv|neet)_.+$"),
            CallbackQueryHandler(edit_mix_list,                 pattern="^edit_mix_list$"),
            CallbackQueryHandler(edit_mix_pick,                 pattern=r"^edit_mix_pick_.+$"),
        ],
        states={
            ADMIN_PASS_STATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_got_pass)],
            # Formula
            FORMULA_CLASS:      [CallbackQueryHandler(afc_class,    pattern=r"^afc_(11|12)$")],
            FORMULA_CHAPTER:    [MessageHandler(filters.TEXT & ~filters.COMMAND, afc_chapter)],
            FORMULA_SUBJ:       [CallbackQueryHandler(afc_subj,     pattern=r"^afs_")],
            FORMULA_FILE:       [
                MessageHandler(filters.PHOTO,                    afc_file),
                MessageHandler(filters.Document.ALL,             afc_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND,  afc_file),
            ],
            # Book
            BOOK_CLASS:         [CallbackQueryHandler(abk_class,    pattern=r"^abk_class_(11|12)$")],
            BOOK_SUBJ:          [CallbackQueryHandler(abk_subj,     pattern=r"^abks_")],
            BOOK_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, abk_name)],
            BOOK_FILES:         [
                MessageHandler(filters.Document.ALL, abk_file),
                CallbackQueryHandler(abk_done, pattern="^abk_done$"),
            ],
            # PYQ
            PYQ_EXAM:           [CallbackQueryHandler(apyq_exam,    pattern=r"^apyq_exam_(mains|adv|neet)$")],
            PYQ_TITLE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, apyq_title)],
            PYQ_FILES:          [
                MessageHandler(filters.Document.ALL, apyq_file),
                CallbackQueryHandler(apyq_done, pattern="^apyq_done$"),
            ],
            # Mix
            MIX_NAME:           [MessageHandler(filters.TEXT & ~filters.COMMAND, amix_name)],
            MIX_FILES:          [
                MessageHandler(filters.Document.ALL, amix_file),
                CallbackQueryHandler(amix_done, pattern="^amix_done$"),
            ],
            # Section management
            SEC_NAME:           [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_sec_got_name)],
            SEC_EMOJI:          [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_sec_got_emoji)],
            # Others
            BROADCAST_TEXT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)],
            DB_CLEAR_PASS_STATE:[MessageHandler(filters.TEXT & ~filters.COMMAND, cleardb_got_pass)],
            # Edit
            EDIT_VALUE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_save)],
        },
        fallbacks=[
            CallbackQueryHandler(admin_panel_cb, pattern="^admin_panel_back$"),
            CommandHandler("start", admin_panel_cb),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
