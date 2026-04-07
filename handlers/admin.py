"""
Admin Panel
- Formula: Upload + Delete (Class→Subject→Chapter→Delete)
- Broadcast
- Stats
- Manage Users (Ban/Unban)
- Clear Database (separate password, User data or Full)
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn, get_all_users
from ui import back_btn, cancel_btn, subject_kb, confirm_delete_kb, E
from config import ADMIN_ID, ADMIN_PASS, DB_CLEAR_PASS
import logging

logger = logging.getLogger(__name__)

# States
(
    ADMIN_PASS_STATE,
    FORMULA_CLASS, FORMULA_CHAPTER, FORMULA_SUBJ, FORMULA_FILE,
    BROADCAST_TEXT,
    DB_CLEAR_PASS_STATE,
) = range(7)

_authed: set = set()


def _is_authed(tg_id: int) -> bool:
    return tg_id == ADMIN_ID and tg_id in _authed


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY / LOGIN
# ════════════════════════════════════════════════════════════════════════════
async def admin_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    if tg_id != ADMIN_ID:
        await query.answer("🛡️ Admin only. This section is restricted.", show_alert=True)
        return ConversationHandler.END
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
        await update.message.reply_text("✅ Authenticated!")
        return await _show_admin_panel_msg(update, context)
    else:
        await update.message.reply_text("❌ Wrong password.", reply_markup=cancel_btn("home"))
        return ADMIN_PASS_STATE


def _admin_kb():
    return Markup([
        [Btn("📐 Formulas",          callback_data="admin_formula_menu"),
         Btn(f"{E['broadcast']} Broadcast", callback_data="admin_broadcast")],
        [Btn(f"{E['stats']} Stats",   callback_data="admin_stats"),
         Btn(f"{E['users']} Users",   callback_data="admin_users")],
        [Btn("🗄️ Clear Database",    callback_data="admin_cleardb")],
        [Btn(f"{E['back']} Back",     callback_data="home")],
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
#  FORMULA MENU — Upload | Browse/Delete
# ════════════════════════════════════════════════════════════════════════════
async def admin_formula_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = Markup([
        [Btn("➕ Upload Formula",    callback_data="admin_formula_add"),
         Btn("🗑️ Delete Formula",   callback_data="admin_formula_del_class")],
        [Btn(f"{E['back']} Back",    callback_data="admin_panel_back")],
    ])
    await query.edit_message_text(
        "📐 *Formula Management*\n\nUpload new formulas or delete existing ones.",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


# ── UPLOAD ───────────────────────────────────────────────────────────────────
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
        "Now send the formula (PDF, image, or text):",
        reply_markup=cancel_btn("admin_formula_menu")
    )
    return FORMULA_FILE


async def afc_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("formula_draft", {})
    file_id = file_type = content = None
    if update.message.photo:
        file_id   = update.message.photo[-1].file_id
        file_type = "photo"
        content   = update.message.caption or ""
    elif update.message.document:
        file_id   = update.message.document.file_id
        file_type = "document"
        content   = update.message.caption or ""
    else:
        content = update.message.text.strip()
    conn = get_conn()
    conn.execute(
        "INSERT INTO formulas (class_num, chapter, subject, file_id, file_type, content, added_by) VALUES (?,?,?,?,?,?,?)",
        (d.get("class_num"), d.get("chapter"), d.get("subject"),
         file_id, file_type, content, update.effective_user.id)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Formula added to *{d.get('chapter')}* — Class {d.get('class_num')} | {d.get('subject')}",
        reply_markup=Markup([
            [Btn("➕ Add Another",   callback_data="admin_formula_add"),
             Btn(f"{E['back']} Back", callback_data="admin_formula_menu")]
        ]), parse_mode="Markdown"
    )
    return ConversationHandler.END


# ── DELETE FORMULA — Class → Subject → Chapter → Entry list ─────────────────
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
    rows = conn.execute(
        "SELECT DISTINCT subject FROM formulas WHERE class_num=? ORDER BY subject", (class_num,)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No formulas for this class.", reply_markup=back_btn("admin_formula_del_class"))
        return ConversationHandler.END
    subjects = [r["subject"] for r in rows if r["subject"]]
    kb_rows = [[Btn(s, callback_data=f"afdel_subj_{class_num}_{s}")] for s in subjects]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data="admin_formula_del_class")])
    await query.edit_message_text(
        f"Select subject (Class {class_num}):",
        reply_markup=Markup(kb_rows)
    )
    return ConversationHandler.END


async def admin_formula_del_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts     = query.data.split("_", 3)
    class_num = parts[2]
    subject   = parts[3]
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT chapter FROM formulas WHERE class_num=? AND subject=? ORDER BY chapter",
        (class_num, subject)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No chapters found.", reply_markup=back_btn(f"afdel_class_{class_num}"))
        return ConversationHandler.END
    chapters = [r["chapter"] for r in rows]
    kb_rows = [[Btn(c, callback_data=f"afdel_entries_{class_num}_{subject}_{c}")] for c in chapters]
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"afdel_class_{class_num}")])
    await query.edit_message_text(
        f"Select chapter to delete from\nClass {class_num} — {subject}:",
        reply_markup=Markup(kb_rows)
    )
    return ConversationHandler.END


async def admin_formula_del_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts     = query.data.split("_", 4)
    class_num = parts[2]
    subject   = parts[3]
    chapter   = parts[4]
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM formulas WHERE class_num=? AND subject=? AND chapter=? ORDER BY id",
        (class_num, subject, chapter)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("No entries found.", reply_markup=back_btn(f"afdel_subj_{class_num}_{subject}"))
        return ConversationHandler.END
    kb_rows = []
    for r in rows:
        label = r["content"][:30] if r["content"] else (r["file_type"] or "file")
        kb_rows.append([Btn(f"🗑️ {label}", callback_data=f"afdel_confirm_{r['id']}")])
    kb_rows.append([Btn("🗑️ Delete ALL entries in this chapter",
                        callback_data=f"afdel_all_confirm_{class_num}_{subject}_{chapter}")])
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=f"afdel_subj_{class_num}_{subject}")])
    await query.edit_message_text(
        f"*{chapter}* — {len(rows)} entries\n\nSelect entry to delete:",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_formula_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fid = int(query.data.split("_")[-1])
    conn = get_conn()
    row = conn.execute("SELECT * FROM formulas WHERE id=?", (fid,)).fetchone()
    conn.close()
    if not row:
        await query.answer("Not found.", show_alert=True)
        return ConversationHandler.END
    await query.edit_message_text(
        f"⚠️ Delete this formula entry?\n*{row['chapter']}* — {row['content'][:50] if row['content'] else row['file_type']}",
        reply_markup=confirm_delete_kb(
            f"afdel_yes_{fid}",
            "admin_formula_menu"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_formula_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fid = int(query.data.split("_")[-1])
    conn = get_conn()
    conn.execute("DELETE FROM formulas WHERE id=?", (fid,))
    conn.commit()
    conn.close()
    await query.edit_message_text("🗑️ Formula entry deleted.", reply_markup=back_btn("admin_formula_menu"))
    return ConversationHandler.END


async def admin_formula_del_all_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # pattern: afdel_all_confirm_11_PHY_Waves
    parts     = query.data.split("_", 4)
    class_num = parts[3]
    rest      = parts[4].split("_", 1)
    subject   = rest[0]
    chapter   = rest[1] if len(rest) > 1 else ""
    context.user_data["del_all"] = {"class_num": class_num, "subject": subject, "chapter": chapter}
    await query.edit_message_text(
        f"⚠️ *This cannot be undone!*\nDelete ALL formulas for:\n\nClass {class_num} | {subject} | *{chapter}*?",
        reply_markup=confirm_delete_kb(
            f"afdel_all_yes",
            "admin_formula_menu"
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def admin_formula_del_all_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = context.user_data.get("del_all", {})
    conn = get_conn()
    conn.execute(
        "DELETE FROM formulas WHERE class_num=? AND subject=? AND chapter=?",
        (d.get("class_num"), d.get("subject"), d.get("chapter"))
    )
    conn.commit()
    conn.close()
    await query.edit_message_text("🗑️ All entries for that chapter deleted.", reply_markup=back_btn("admin_formula_menu"))
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
    tasks       = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    reports     = conn.execute("SELECT COUNT(*) FROM daily_reports").fetchone()[0]
    conn.close()
    text = (
        f"📊 *Bot Stats*\n\n"
        f"👥 Total Users: {total_users}\n"
        f"🚫 Banned: {banned}\n"
        f"🧠 Memories: {memories}\n"
        f"📐 Formulas: {formulas}\n"
        f"📝 Tasks: {tasks}\n"
        f"📒 Reports: {reports}"
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
        label  = f"{u['name'] or 'Unknown'} ({status})"
        action = "✅ Unban" if u["is_banned"] else "🚫 Ban"
        rows.append([
            Btn(label[:35], callback_data="noop"),
            Btn(action, callback_data=f"admin_toggle_{u['tg_id']}")
        ])
    rows.append([Btn(f"{E['back']} Back", callback_data="admin_panel_back")])
    await query.edit_message_text(
        f"👥 *User Management* (last 20)",
        reply_markup=Markup(rows), parse_mode="Markdown"
    )
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
            msg = "🚫 You have been banned from JEE Saarthi." if new_ban else "✅ You have been unbanned! Welcome back!"
            await context.bot.send_message(target_id, msg)
        except Exception:
            pass
    conn.close()
    await admin_users(update, context)


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
        "👥 *User Data* — Deletes all user tasks, memories, reports, scores, doubts, revisions, study logs. "
        "Formulas and user accounts are kept.\n\n"
        "💥 *Everything* — Deletes ALL data including formulas and user accounts.\n\n"
        "⚠️ Both require a separate confirmation password.",
        reply_markup=kb, parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cleardb_user_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cleardb_type"] = "user"
    await query.edit_message_text(
        "🔐 Enter the *database clear password* to confirm:\n\n"
        "_(This is different from your admin password)_",
        reply_markup=cancel_btn("admin_cleardb"), parse_mode="Markdown"
    )
    return DB_CLEAR_PASS_STATE


async def cleardb_all_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cleardb_type"] = "all"
    await query.edit_message_text(
        "🔐 Enter the *database clear password* to confirm:\n\n"
        "_(This is different from your admin password)_",
        reply_markup=cancel_btn("admin_cleardb"), parse_mode="Markdown"
    )
    return DB_CLEAR_PASS_STATE


async def cleardb_all_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cleardb_type"] = "all"
    await query.edit_message_text(
        "🔐 Enter the *database clear password* to confirm:\n\n"
        "_(This is different from your admin password)_",
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
        # Delete all user data EXCEPT formulas and user accounts
        for table in ["tasks", "memories", "daily_reports", "thoughts", "motivation",
                      "study_log", "test_scores", "revision_schedule", "doubts", "lectures"]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        await update.message.reply_text(
            "✅ *User data cleared!*\n\nAll tasks, memories, reports, scores, doubts, "
            "revisions, study logs deleted.\nFormulas and user accounts are intact.",
            reply_markup=back_btn("admin_panel_back"), parse_mode="Markdown"
        )
    else:
        # Delete EVERYTHING
        for table in ["tasks", "memories", "daily_reports", "thoughts", "motivation",
                      "study_log", "test_scores", "revision_schedule", "doubts", "lectures",
                      "formulas", "users"]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.close()
        _authed.discard(update.effective_user.id)
        await update.message.reply_text(
            "💥 *Full database cleared!*\n\nAll data including formulas and user accounts deleted.\n"
            "Use /start to re-register.",
            parse_mode="Markdown"
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
            CallbackQueryHandler(admin_broadcast_start,         pattern="^admin_broadcast$"),
            CallbackQueryHandler(admin_stats,                   pattern="^admin_stats$"),
            CallbackQueryHandler(admin_users,                   pattern="^admin_users$"),
            CallbackQueryHandler(admin_toggle_ban,              pattern=r"^admin_toggle_\d+$"),
            CallbackQueryHandler(admin_cleardb,                 pattern="^admin_cleardb$"),
            CallbackQueryHandler(cleardb_user_ask,              pattern="^cleardb_user$"),
            CallbackQueryHandler(cleardb_all_ask,               pattern="^cleardb_all$"),
        ],
        states={
            ADMIN_PASS_STATE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_got_pass)],
            FORMULA_CLASS:     [CallbackQueryHandler(afc_class,   pattern=r"^afc_(11|12)$")],
            FORMULA_CHAPTER:   [MessageHandler(filters.TEXT & ~filters.COMMAND, afc_chapter)],
            FORMULA_SUBJ:      [CallbackQueryHandler(afc_subj,    pattern=r"^afs_")],
            FORMULA_FILE:      [
                MessageHandler(filters.PHOTO,            afc_file),
                MessageHandler(filters.Document.ALL,     afc_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, afc_file),
            ],
            BROADCAST_TEXT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)],
            DB_CLEAR_PASS_STATE:[MessageHandler(filters.TEXT & ~filters.COMMAND, cleardb_got_pass)],
        },
        fallbacks=[
            CallbackQueryHandler(admin_panel_cb, pattern="^admin_panel_back$"),
            CommandHandler("start", admin_panel_cb),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
