from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn, get_all_users
from ui import back_btn, cancel_btn, subject_kb, E
from config import ADMIN_ID, ADMIN_PASS
import logging

logger = logging.getLogger(__name__)

# ── States ──────────────────────────────────────────────────────────────────
(
    ADMIN_PASS_STATE,
    FORMULA_CLASS, FORMULA_CHAPTER, FORMULA_SUBJ, FORMULA_FILE,
    BROADCAST_TEXT,
) = range(6)

_authed: set = set()   # session-authed admin tg_ids


def _is_authed(tg_id: int) -> bool:
    return tg_id == ADMIN_ID and tg_id in _authed


# ════════════════════════════════════════════════════════════════════════════
#  ENTRY
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


async def _show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    kb = _admin_kb()
    await query.edit_message_text("🛡️ *Admin Panel*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def _show_admin_panel_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = _admin_kb()
    await update.message.reply_text("🛡️ *Admin Panel*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


def _admin_kb():
    return Markup([
        [Btn("➕ Add Formula",    callback_data="admin_formula_add"),
         Btn(f"{E['broadcast']} Broadcast", callback_data="admin_broadcast")],
        [Btn(f"{E['stats']} Stats",          callback_data="admin_stats"),
         Btn(f"{E['users']} Manage Users",   callback_data="admin_users")],
        [Btn(f"{E['back']} Back",            callback_data="home")],
    ])


async def admin_panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _is_authed(update.effective_user.id):
        await query.answer("Session expired. Go back and login again.", show_alert=True)
        return ConversationHandler.END
    await query.edit_message_text("🛡️ *Admin Panel*", reply_markup=_admin_kb(), parse_mode="Markdown")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  ADD FORMULA
# ════════════════════════════════════════════════════════════════════════════
async def admin_formula_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop("formula_draft", None)
    kb = Markup([
        [Btn("Class 11", callback_data="afc_11"),
         Btn("Class 12", callback_data="afc_12")],
        [Btn(f"{E['cancel']} Cancel", callback_data="admin_panel_back")],
    ])
    await query.edit_message_text("➕ *Add Formula*\n\nSelect class:", reply_markup=kb, parse_mode="Markdown")
    return FORMULA_CLASS


async def afc_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["formula_draft"] = {"class_num": query.data.split("_")[1]}
    await query.edit_message_text(
        "Enter chapter name:",
        reply_markup=cancel_btn("admin_panel_back")
    )
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
        "Now send the formula file (PDF, image) or text:",
        reply_markup=cancel_btn("admin_panel_back")
    )
    return FORMULA_FILE


async def afc_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data.get("formula_draft", {})
    file_id = None
    file_type = None
    content = None
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
        content = update.message.caption or ""
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
        content = update.message.caption or ""
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
        f"✅ Formula added to *{d.get('chapter')}* (Class {d.get('class_num')})!",
        reply_markup=back_btn("admin_panel_back"), parse_mode="Markdown"
    )
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
    text = update.message.text.strip()
    users = get_all_users()
    sent = 0
    failed = 0
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
    banned = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    memories = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    formulas = conn.execute("SELECT COUNT(*) FROM formulas").fetchone()[0]
    tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    reports = conn.execute("SELECT COUNT(*) FROM daily_reports").fetchone()[0]
    conn.close()
    text = (
        f"{E['stats']} *Bot Stats*\n\n"
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
        label = f"{u['name'] or 'Unknown'} ({'BANNED' if u['is_banned'] else 'active'})"
        action = "unban" if u["is_banned"] else "ban"
        rows.append([Btn(label[:40], callback_data="noop"),
                     Btn(f"{'✅ Unban' if u['is_banned'] else '🚫 Ban'}", callback_data=f"admin_toggle_{u['tg_id']}")])
    rows.append([Btn(f"{E['back']} Back", callback_data="admin_panel_back")])
    await query.edit_message_text(
        f"{E['users']} *User Management* (last 20)",
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
            msg = "🚫 You have been banned." if new_ban else "✅ You have been unbanned!"
            await context.bot.send_message(target_id, msg)
        except Exception:
            pass
    conn.close()
    await admin_users(update, context)


# ════════════════════════════════════════════════════════════════════════════
#  BUILD
# ════════════════════════════════════════════════════════════════════════════
def build_admin_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_home,             pattern="^admin_home$"),
            CallbackQueryHandler(admin_panel_cb,         pattern="^admin_panel_back$"),
            CallbackQueryHandler(admin_formula_add,      pattern="^admin_formula_add$"),
            CallbackQueryHandler(admin_broadcast_start,  pattern="^admin_broadcast$"),
            CallbackQueryHandler(admin_stats,            pattern="^admin_stats$"),
            CallbackQueryHandler(admin_users,            pattern="^admin_users$"),
            CallbackQueryHandler(admin_toggle_ban,       pattern=r"^admin_toggle_\d+$"),
        ],
        states={
            ADMIN_PASS_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_got_pass)],
            FORMULA_CLASS:    [CallbackQueryHandler(afc_class,    pattern=r"^afc_(11|12)$")],
            FORMULA_CHAPTER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, afc_chapter)],
            FORMULA_SUBJ:     [CallbackQueryHandler(afc_subj,     pattern=r"^afs_")],
            FORMULA_FILE:     [
                MessageHandler(filters.PHOTO,    afc_file),
                MessageHandler(filters.Document.ALL, afc_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, afc_file),
            ],
            BROADCAST_TEXT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)],
        },
        fallbacks=[
            CallbackQueryHandler(admin_panel_cb, pattern="^admin_panel_back$"),
            CommandHandler("start", admin_panel_cb),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
