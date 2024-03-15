import html
import json
import logging
import re
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from tg_blog_updater import utils

# GITHUB_TOKEN = "YOUR_GITHUB_ACCESS_TOKEN"
# GITHUB_REPO_NAME = "YOUR_GITHUB_USERNAME/YOUR_REPO_NAME"

# # Initialize GitHub client
# # g = Github(GITHUB_TOKEN)
# # repo = g.get_repo(GITHUB_REPO_NAME)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# set higher level for httpx to avoid GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Log the error and send a telegram message to notify the developer."""

    # Log the error before we do anything else.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns usual python message about exception
    # list of strings rather than a single string, so we have to join them.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build message with markup & additional information about what happened.
    # You need to add some logic to deal with messages longer than the 4096.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=utils.get_env("DEBUG_CHAT_ID"),
        text=message,
        parse_mode=ParseMode.HTML,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        f"Hi {update.effective_user.first_name}!\n"
        "Send message with this format to update your blog:\n\n"
        f"<pre>Title: Your Title\n===\nYour post content"
        "</pre>"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode=ParseMode.HTML,
    )


async def handle_message(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    match = re.match(r"(.+)\n===\n(.+)", message, re.DOTALL)
    if match:
        title, body = match.groups()
        create_post(title, body)
        await update.message.reply_text("Post created successfully!")
    else:
        await update.message.reply_text(
            "Invalid message format. Please use the format:\n\nYour Title\n===\nYour post content."
        )


def create_post(title: str, body: str) -> None:
    # Format the title to be URL-friendly
    filename = title.lower().replace(" ", "-") + ".md"
    file_path = f"_posts/{filename}"

    # Create the post content
    content = f"---\ntitle: {title}\n---\n\n{body}"

    print(file_path)
    print(content)

    # Create a new file in the repository
    # repo.create_file(file_path, f"Create new post: {title}", content)


def main() -> None:
    app = (
        ApplicationBuilder()
        .token(utils.get_env("TELEGRAM_TOKEN"))
        .base_url(utils.get_env("TELEGRAM_BASE_URL", "https://api.telegram.org/bot"))
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters=filters.TEXT & ~filters.COMMAND,
            callback=handle_message,
        )
    )
    app.add_error_handler(error_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
