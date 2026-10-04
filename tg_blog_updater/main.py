"""Telegram handlers that publish Jekyll posts through the GitHub API."""

import asyncio
import functools
import html
import json
import logging
import traceback

from github import Auth, Github, GithubException
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from tg_blog_updater import posts, utils

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096
FORMAT_HELP = "Your Title\n===\nYour tags (comma separated)\n===\nYour post content"


class PostExistsError(Exception):
    """A post with this date and slug is already in the repository."""

    def __init__(self, path: str) -> None:
        super().__init__(f"A post already exists at {path}")
        self.path = path


def _require_chat_id(name: str) -> str:
    value = utils.get_env(name)
    try:
        int(value)
    except ValueError as exc:
        raise utils.MissingEnvironmentVariable(
            f"Environment variable {name} must be an integer chat id"
        ) from exc
    return value


@functools.lru_cache(maxsize=1)
def get_repository():
    """Authenticated repository used for new posts.

    The client is created on first use so importing this module does not
    require GitHub credentials.
    """

    client = Github(auth=Auth.Token(utils.get_env("GITHUB_TOKEN")))
    return client.get_repo(utils.get_env("GITHUB_REPO_NAME").lower())


def create_post(title: str, tags: str, body: str) -> str:
    """Commit a new post and return the commit SHA."""

    now = posts.current_time()
    file_path = posts.build_file_path(
        title,
        now,
        utils.get_env("POST_PATH", "_posts"),
    )
    content = posts.render_post(title, tags, body, now)

    try:
        result = get_repository().create_file(
            file_path,
            f"Create new post: {title}",
            content,
        )
    except GithubException as exc:
        if _is_existing_file_error(exc):
            raise PostExistsError(file_path) from exc
        raise

    sha = result["commit"].sha
    if not sha:
        raise RuntimeError(f"GitHub did not return a commit for {file_path}")

    logger.info("Post created: %s (%s)", file_path, sha)
    return sha


def _is_existing_file_error(exc: GithubException) -> bool:
    if exc.status != 422 or not isinstance(exc.data, dict):
        return False
    message = str(exc.data.get("message", "")).lower()
    return "sha" in message


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _html_pre(text: str, limit: int) -> str:
    return f"<pre>{_clip(html.escape(text), limit)}</pre>"


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Log the error and notify DEBUG_CHAT_ID, within Telegram's size limit."""

    logger.error("Exception while handling an update:", exc_info=context.error)

    error = context.error
    if isinstance(error, BaseException):
        tb_string = "".join(traceback.format_exception(error))
    else:
        tb_string = str(error)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    update_dump = json.dumps(update_str, indent=2, ensure_ascii=False)
    message = (
        "An exception was raised while handling an update\n"
        f"{_html_pre(update_dump, 800)}\n"
        f"{_html_pre(tb_string, 2500)}"
    )

    try:
        await context.bot.send_message(
            chat_id=utils.get_env("DEBUG_CHAT_ID"),
            text=_clip(message, TELEGRAM_MESSAGE_LIMIT),
            parse_mode=ParseMode.HTML,
        )
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to send the error notification")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Explain the message format."""

    message = update.effective_message
    if message is None:
        return

    user = update.effective_user
    name = user.first_name if user is not None and user.first_name else "there"
    text = (
        f"Hi {html.escape(name)}!\n"
        "Send a message in this format to publish a post:\n\n"
        f"<pre>{html.escape(FORMAT_HELP)}</pre>"
    )
    await context.bot.send_message(
        chat_id=message.chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a post from a message in the configured chat."""

    del context
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or not message.text:
        return

    if chat.id != int(utils.get_env("CHAT_ID")):
        logger.info("Rejected message from chat %s", chat.id)
        await message.reply_text(
            "This bot is only available to work in selected chats."
        )
        return

    parsed = posts.parse_message(message.text)
    if parsed is None:
        await message.reply_text(
            "Invalid message format. Please use the format:\n\n" + FORMAT_HELP
        )
        return

    title, tags, body = parsed
    try:
        await asyncio.to_thread(create_post, title, tags, body)
    except PostExistsError:
        await message.reply_text(
            "A post with this title already exists for today. "
            "Change the title and send it again."
        )
        return

    await message.reply_text("Post created successfully!")


def _configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _require_runtime_config() -> None:
    utils.get_env("TELEGRAM_TOKEN")
    _require_chat_id("CHAT_ID")
    _require_chat_id("DEBUG_CHAT_ID")
    posts.blog_timezone()
    get_repository()


def main() -> None:
    """Validate configuration, then poll Telegram."""

    _configure_logging()
    _require_runtime_config()

    app = (
        ApplicationBuilder()
        .token(utils.get_env("TELEGRAM_TOKEN"))
        .base_url(utils.get_env("TELEGRAM_BASE_URL", "https://api.telegram.org/bot"))
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
