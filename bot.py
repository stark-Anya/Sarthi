"""
JEE Saarthi — Main Bot Entry
All ConversationHandlers are instantiated DIRECTLY here.
NO get_conversation_handler() functions are used anywhere.
"""

import logging
import sys
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
)
from database import init_db
from config import BOT_TOKEN
from scheduler import setup_scheduler

# ── Handlers ────────────────────────────────────────────────────────────────
from handlers import common
from handlers import search as search_handler

# Import build functions (NOT get_conversation_handler)
from handlers.today      import build_today_conv
from handlers.memories   import build_mem_conv
from handlers.formulas   import build_formula_conv
from handlers.motivation import build_motiv_conv, build_thought_conv
from handlers.admin      import build_admin_conv

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ── Commands ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",  common.start))
    app.add_handler(CommandHandler("search", search_handler.search_cmd))
    app.add_handler(CommandHandler("ban",    common.ban_user))
    app.add_handler(CommandHandler("unban",  common.unban_user))

    # ── ConversationHandlers — instantiated DIRECTLY, no wrapper functions ──
    today_conv   = build_today_conv()
    mem_conv     = build_mem_conv()
    formula_conv = build_formula_conv()
    motiv_conv   = build_motiv_conv()
    thought_conv = build_thought_conv()
    admin_conv   = build_admin_conv()

    app.add_handler(today_conv)
    app.add_handler(mem_conv)
    app.add_handler(formula_conv)
    app.add_handler(motiv_conv)
    app.add_handler(thought_conv)
    app.add_handler(admin_conv)

    # ── Global CallbackQuery handlers (after ConversationHandlers) ───────────
    app.add_handler(CallbackQueryHandler(common.home_callback, pattern="^home$"))
    app.add_handler(CallbackQueryHandler(common.noop,          pattern="^noop$"))

    # ── Scheduler ────────────────────────────────────────────────────────────
    setup_scheduler(app)

    logger.info("JEE Saarthi bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
