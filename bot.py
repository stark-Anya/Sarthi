"""
JEE Saarthi — Main Bot Entry
All ConversationHandlers instantiated DIRECTLY. NO get_conversation_handler().
"""
import logging
import sys
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
)
from database import init_db
from config import BOT_TOKEN
from scheduler import setup_scheduler

from handlers import common
from handlers import search as search_handler
from handlers.today      import build_today_conv
from handlers.memories   import build_mem_conv
from handlers.formulas   import build_formula_conv
from handlers.materials  import build_materials_conv
from handlers.motivation import build_motiv_conv, build_thought_conv
from handlers.admin      import build_admin_conv

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

    # Commands
    app.add_handler(CommandHandler("start",  common.start))
    app.add_handler(CommandHandler("search", search_handler.search_cmd))
    app.add_handler(CommandHandler("ban",    common.ban_user))
    app.add_handler(CommandHandler("unban",  common.unban_user))

    # ConversationHandlers — directly instantiated
    app.add_handler(build_today_conv())
    app.add_handler(build_mem_conv())
    app.add_handler(build_materials_conv())   # Materials: Books + Formulas
    app.add_handler(build_formula_conv())     # direct formula_home access (from materials)
    app.add_handler(build_motiv_conv())
    app.add_handler(build_thought_conv())
    app.add_handler(build_admin_conv())

    # Global callbacks
    app.add_handler(CallbackQueryHandler(common.home_callback,                  pattern="^home$"))
    app.add_handler(CallbackQueryHandler(common.noop,                           pattern="^noop$"))

    # Search inline callbacks (delete from search results)
    app.add_handler(CallbackQueryHandler(search_handler.search_show_answer,     pattern=r"^search_ans_(silly|error|important)_\d+$"))
    app.add_handler(CallbackQueryHandler(search_handler.search_del_confirm,     pattern=r"^search_del_confirm_(silly|error|important)_\d+$"))
    app.add_handler(CallbackQueryHandler(search_handler.search_del_yes,         pattern=r"^search_del_yes_(silly|error|important)_\d+$"))

    setup_scheduler(app)
    logger.info("JEE Saarthi bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
