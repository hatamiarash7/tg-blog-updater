"""Telegram bot to update a Jekyll blog via messages."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .handlers import error_handler, handle_callback_query, handle_message
from .utils import get_env

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# set higher level for httpx to avoid GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if not update.effective_chat or not update.effective_user:
        logger.warning("Update does not contain effective chat or user.")
        return
    message = (
        f"Hi {update.effective_user.first_name}!\n"
        "Send message with this format to update your blog:\n\n"
        """<pre>Your Title\n===\n
        +category\n#tag\n@author\n&layout\n/path\n===\n
        Your post content"""
        "</pre>"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode=ParseMode.HTML,
    )


def main() -> None:
    """Start the bot."""
    app = (
        ApplicationBuilder()
        .token(get_env("TELEGRAM_TOKEN"))
        .base_url(get_env("TELEGRAM_BASE_URL", "https://api.telegram.org/bot"))
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            callback=handle_message,
        )
    )
    app.add_error_handler(error_handler)
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
