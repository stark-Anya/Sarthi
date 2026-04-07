from telegram import Update
from telegram.ext import ContextTypes
from database import upsert_user, get_user, is_banned
from ui import home_kb
from config import ADMIN_ID
from datetime import date
import logging

logger = logging.getLogger(__name__)


async def check_banned(update: Update) -> bool:
    tg_id = update.effective_user.id
    if is_banned(tg_id):
        if update.callback_query:
            await update.callback_query.answer("🚫 You are banned from using this bot.", show_alert=True)
        else:
            await update.message.reply_text("🚫 You are banned from using this bot.")
        return True
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_banned(update):
        return
    user = update.effective_user
    upsert_user(user.id, user.full_name)
    db_user = get_user(user.id)
    streak = db_user["streak"] if db_user else 0
    today_str = date.today().strftime("%A, %d %B %Y")
    text = (
        f"👋 *Welcome back, {user.first_name}!*\n\n"
        f"📅 {today_str}\n"
        f"🔥 Current Streak: *{streak} day(s)*\n\n"
        f"What would you like to do today?"
    )
    await update.message.reply_text(text, reply_markup=home_kb(), parse_mode="Markdown")


async def home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await check_banned(update):
        return
    user = update.effective_user
    db_user = get_user(user.id)
    streak = db_user["streak"] if db_user else 0
    today_str = date.today().strftime("%A, %d %B %Y")
    text = (
        f"🏠 *Home*\n\n"
        f"📅 {today_str}\n"
        f"🔥 Streak: *{streak} day(s)*\n\n"
        f"Choose a section:"
    )
    await query.edit_message_text(text, reply_markup=home_kb(), parse_mode="Markdown")


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return
    from database import get_conn
    conn = get_conn()
    conn.execute("UPDATE users SET is_banned=1 WHERE tg_id=?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ User {target_id} has been banned.")
    try:
        await context.bot.send_message(target_id, "🚫 You have been banned from JEE Saarthi.")
    except Exception:
        pass


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return
    from database import get_conn
    conn = get_conn()
    conn.execute("UPDATE users SET is_banned=0 WHERE tg_id=?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ User {target_id} has been unbanned.")
    try:
        await context.bot.send_message(target_id, "✅ You have been unbanned from JEE Saarthi. Welcome back!")
    except Exception:
        pass


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
