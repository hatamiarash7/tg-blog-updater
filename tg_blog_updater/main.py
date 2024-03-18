import html
import json
import logging
import re
import traceback
from datetime import datetime

from slugify import slugify
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
from github import Github
from github import Auth

from tg_blog_updater import utils

github = Github(
    auth=Auth.Token(
        utils.get_env("GITHUB_TOKEN"),
    ),
)
repo = github.get_repo(utils.get_env("GITHUB_REPO_NAME").lower())

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
        f"<pre>Your Title\n===\nYour tags ( Comma Separated )\n===\nYour post content"
        "</pre>"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode=ParseMode.HTML,
    )


async def handle_message(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.id != int(utils.get_env("CHAT_ID")):
        logger.debug(f"Chat ID: {update.effective_chat.id} rejected")
        await update.message.reply_text(
            "This bot is only available to work in selected chats."
        )
        return

    message = update.message.text
    match = re.match(r"(.+)\n===\n(.+)\n===\n(.+)", message, re.DOTALL)
    if match:
        title, tags, body = match.groups()
        create_post(title, tags, body)
        await update.message.reply_text("Post created successfully!")
    else:
        await update.message.reply_text(
            "Invalid message format. Please use the format:\n\nYour Title\n===\nYour tags ( Comma Separated )\n===\nYour post content."
        )


def create_post(title: str, tags: str, body: str) -> None:
    # Format the title to be URL-friendly
    now = datetime.now()

    filename = f"{now.strftime('%Y-%m-%d')}"
    filename += f"-{slugify(text=title, lowercase=True, allow_unicode=False)}.md"
    file_path = f"{utils.get_env('POST_PATH', '_posts')}/{filename}"

    # Create the post content
    content = f"---\ntitle: {title}\ndate: {now.strftime('%Y-%m-%d %H:%M:%S')} +3:30\n"
    content += f"tags: [{ ', '.join(tags.split('-')) }]\n---\n\n{body}"

    # Create a new file in the repository
    result = repo.create_file(file_path, f"Create new post: {title}", content)
    if result and result["commit"].sha:
        logger.info(f"Post created successfully! - {result['commit'].sha}")
    else:
        logger.error(f"Failed to create post! - {filename}")


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
