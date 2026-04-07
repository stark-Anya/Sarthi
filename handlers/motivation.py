"""
Motivation & Thought Vault
- Add + Delete + Nav (both)
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database import get_conn
from ui import back_btn, cancel_btn, confirm_delete_kb, nav_kb, E
from handlers.common import check_banned
import logging

logger = logging.getLogger(__name__)

VAULT_ADD = 0


def _uid(update: Update):
    conn = get_conn()
    row = conn.execute("SELECT id FROM users WHERE tg_id=?",
                       (update.effective_user.id,)).fetchone()
    conn.close()
    return row["id"] if row else None


# ─── Generic vault helpers ───────────────────────────────────────────────────

async def _vault_home(update, context, table, label, emoji, add_cb, nav_cb, del_cb_prefix, back_cb):
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    conn = get_conn()
    count = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id=?", (uid,)).fetchone()[0]
    conn.close()
    kb_rows = [
        [Btn(f"➕ Add {label}", callback_data=add_cb)],
    ]
    if count:
        kb_rows.append([Btn(f"👁️ View All ({count})", callback_data=f"{nav_cb}_0")])
    else:
        kb_rows.append([Btn(f"No {label.lower()}s yet", callback_data="noop")])
    kb_rows.append([Btn(f"{E['back']} Back", callback_data=back_cb)])
    await query.edit_message_text(
        f"{emoji} *{label} Vault*\n\n{count} item(s) saved.",
        reply_markup=Markup(kb_rows), parse_mode="Markdown"
    )
    return ConversationHandler.END


async def _vault_add_start(update, context, label, cancel_cb):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"➕ *Add {label}*\n\nSend text or image:",
        reply_markup=cancel_btn(cancel_cb), parse_mode="Markdown"
    )
    return VAULT_ADD


async def _vault_save(update, context, table, label, home_cb):
    if await check_banned(update):
        return ConversationHandler.END
    uid = _uid(update)
    if update.message.photo:
        file_id   = update.message.photo[-1].file_id
        file_type = "photo"
        content   = update.message.caption or ""
    else:
        content   = update.message.text.strip()
        file_id   = None
        file_type = None
    conn = get_conn()
    conn.execute(
        f"INSERT INTO {table} (user_id, content, file_id, file_type) VALUES (?,?,?,?)",
        (uid, content, file_id, file_type)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ {label} saved!",
        reply_markup=back_btn(home_cb)
    )
    return ConversationHandler.END


async def _vault_nav(update, context, table, label, nav_prefix, home_cb, del_prefix):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[-1])
    uid = _uid(update)
    conn = get_conn()
    items = conn.execute(
        f"SELECT * FROM {table} WHERE user_id=? ORDER BY created DESC", (uid,)
    ).fetchall()
    conn.close()
    if not items:
        await query.edit_message_text(f"No {label.lower()}s yet.", reply_markup=back_btn(home_cb))
        return ConversationHandler.END
    idx = max(0, min(idx, len(items) - 1))
    it  = items[idx]
    text = f"*{label}*\n🗓 {it['created'][:10]}\n\n{it['content'] or ''}"
    extra = [
        [Btn("🗑️ Delete this", callback_data=f"{del_prefix}_{it['id']}_back_{home_cb}")],
        [Btn(f"{E['back']} Back", callback_data=home_cb)],
    ]
    kb = nav_kb(nav_prefix, idx, len(items), extra)
    if it["file_id"] and it["file_type"] == "photo":
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_photo(
            update.effective_user.id,
            photo=it["file_id"], caption=text,
            reply_markup=kb, parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


async def _vault_del_confirm(update, context, nav_prefix, home_cb):
    query = update.callback_query
    await query.answer()
    # pattern: motiv_delconfirm_42_back_motiv_home
    parts  = query.data.split("_")
    item_id = int(parts[2])
    await query.edit_message_text(
        "⚠️ *This cannot be undone.* Delete this entry?",
        reply_markup=confirm_delete_kb(
            f"{nav_prefix}_delyes_{item_id}",
            home_cb
        ),
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def _vault_del_yes(update, context, table, home_cb):
    query = update.callback_query
    await query.answer()
    parts   = query.data.split("_")
    item_id = int(parts[2])
    conn = get_conn()
    conn.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    await query.edit_message_text("🗑️ Deleted.", reply_markup=back_btn(home_cb))
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════════
#  MOTIVATION
# ════════════════════════════════════════════════════════════════════════════
async def motiv_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_home(update, context, "motivation", "Motivation", "🔥",
                             "motiv_add", "motiv_nav", "motiv_delconfirm", "home")

async def motiv_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_add_start(update, context, "Motivation", "motiv_home")

async def motiv_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_save(update, context, "motivation", "Motivation", "motiv_home")

async def motiv_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_nav(update, context, "motivation", "🔥 Motivation",
                            "motiv_nav", "motiv_home", "motiv_delconfirm")

async def motiv_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_del_confirm(update, context, "motiv", "motiv_home")

async def motiv_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_del_yes(update, context, "motivation", "motiv_home")

async def motiv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🔥 Motivation Vault", reply_markup=back_btn("home")
        )
    return ConversationHandler.END

def build_motiv_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(motiv_home,        pattern="^motiv_home$"),
            CallbackQueryHandler(motiv_add_start,   pattern="^motiv_add$"),
            CallbackQueryHandler(motiv_nav,         pattern=r"^motiv_nav_\d+$"),
            CallbackQueryHandler(motiv_del_confirm, pattern=r"^motiv_delconfirm_\d+_back_.+$"),
            CallbackQueryHandler(motiv_del_yes,     pattern=r"^motiv_delyes_\d+$"),
        ],
        states={
            VAULT_ADD: [
                MessageHandler(filters.PHOTO,                motiv_save),
                MessageHandler(filters.TEXT & ~filters.COMMAND, motiv_save),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(motiv_cancel, pattern="^motiv_home$"),
            CommandHandler("start", motiv_cancel),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )


# ════════════════════════════════════════════════════════════════════════════
#  THOUGHTS
# ════════════════════════════════════════════════════════════════════════════
async def thought_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_home(update, context, "thoughts", "Thought", "💭",
                             "thought_add", "thought_nav", "thought_delconfirm", "home")

async def thought_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_add_start(update, context, "Thought", "thought_home")

async def thought_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_save(update, context, "thoughts", "Thought", "thought_home")

async def thought_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_nav(update, context, "thoughts", "💭 Thought",
                            "thought_nav", "thought_home", "thought_delconfirm")

async def thought_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_del_confirm(update, context, "thought", "thought_home")

async def thought_del_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _vault_del_yes(update, context, "thoughts", "thought_home")

async def thought_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "💭 Thoughts Vault", reply_markup=back_btn("home")
        )
    return ConversationHandler.END

def build_thought_conv():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(thought_home,        pattern="^thought_home$"),
            CallbackQueryHandler(thought_add_start,   pattern="^thought_add$"),
            CallbackQueryHandler(thought_nav,         pattern=r"^thought_nav_\d+$"),
            CallbackQueryHandler(thought_del_confirm, pattern=r"^thought_delconfirm_\d+_back_.+$"),
            CallbackQueryHandler(thought_del_yes,     pattern=r"^thought_delyes_\d+$"),
        ],
        states={
            VAULT_ADD: [
                MessageHandler(filters.PHOTO,                thought_save),
                MessageHandler(filters.TEXT & ~filters.COMMAND, thought_save),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(thought_cancel, pattern="^thought_home$"),
            CommandHandler("start", thought_cancel),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
