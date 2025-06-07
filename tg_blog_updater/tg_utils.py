"""Helper functions for Telegram-based functions."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image
from slugify import slugify
from telegram.constants import ParseMode

from .utils import ExtrasNotEnabledError, get_env

if TYPE_CHECKING:
    import logging
    from datetime import datetime

    from telegram import Bot, File, Update
    from telegram.ext import ContextTypes


ASSETS_ROOT = Path(get_env("ASSETS_PATH", "assets"))
CHAT_ID = int(get_env("CHAT_ID"))
EXTRAS_ENABLED = get_env("EXTRAS_ENABLED", "false").lower() in {"true", "1", "yes"}
MAX_LENGTH = 4096  # Telegram message length limit


def get_asset_filename(
    message_text: str, date: datetime, user_data: dict[str, int | str]
) -> str:
    """Get the filename for the asset based on user data or message text.

    Returns:
        str: The filename to use for the asset.

    """

    def slugify_title(message_text: str, date: datetime) -> str:
        """Return a slugified title for a new post.

        Returns:
            str: A slugified title for the post.

        """
        first_line = next(
            iter(message_text.splitlines()),
            f"{date.strftime('%Y-%m-%d_%H-%M-%S')}-untitled",
        )
        return slugify(first_line, lowercase=True, separator="_")

    if not user_data.get("short_title"):
        user_data["short_title"] = slugify_title(message_text, date)
        user_data["asset_num"] = 0

    user_data["asset_num"] = int(user_data.get("asset_num", 0)) + 1

    return f"{user_data['short_title']}-{user_data['asset_num']}"


async def get_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    logger: logging.Logger,
) -> bytes | None:
    """Get a photo from the Telegram message.

    Returns:
        bytes: The photo content if available, otherwise None.

    """
    if update.message is None:
        logger.error("Update.message is missing.")
        return None

    if not update.message.photo:
        return None

    best_photo = update.message.photo[-1]  # highest resolution
    tg_file: File = await context.bot.get_file(best_photo.file_id)

    return to_webps(bytes(await tg_file.download_as_bytearray()))


def to_webps(photo_bytes: bytes) -> bytes:
    """Convert a .jpg or .png photo in bytes to .webp in bytes.

    Returns:
        bytes: The photo content in WEBP format.

    """
    image = Image.open(io.BytesIO(photo_bytes))

    output_buffer = io.BytesIO()
    image.save(output_buffer, format="WEBP")

    return output_buffer.getvalue()


async def get_video(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    logger: logging.Logger,
) -> bytes | None:
    """Get a video from the Telegram message.

    Args:
        update (Update): The Telegram update containing the message.
        context (ContextTypes.DEFAULT_TYPE): The context of the update.
        title (str): The title to use for slugifying the assets.
        logger (logging.Logger): Logger instance for logging errors.

    Returns:
        tuple[str, bytes] | None: A tuple containing the filename and
            video content in bytes or None if no video is found.

    """
    tg_file: File | None = None

    if update.message is None:
        logger.error("Update.message is missing.")
        return None

    if not update.message.video:
        return None

    tg_file = await context.bot.get_file(update.message.video.file_id)
    logger.debug("Video file path: %s", tg_file.file_path)

    return bytes(await tg_file.download_as_bytearray())


async def get_asset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    logger: logging.Logger,
) -> tuple[Path | None, bytes | None]:
    """Get an asset (photo or video) from the Telegram message.

    Raises:
        ExtrasNotEnabledError: If video support is requested but not enabled.

    Returns:
        tuple[Path | None, bytes | None]: A tuple containing the asset filename and
            content in bytes or (None, None) if no asset is found.

    """
    if context.user_data is None or not update.message or not update.effective_message:
        logger.warning("Invalid update or context, skipping asset retrieval.")
        return None, None

    message_text: str = update.message.text or update.message.caption or ""

    logger.info(
        "Processing message with title: %s",
        context.user_data.get("short_title", "Untitled"),
    )

    if asset_content := await get_photo(
        update,
        context,
        logger,
    ):
        suffix = ".webp"  # we got a photo
    elif asset_content := await get_video(
        update,
        context,
        logger,
    ):
        suffix = ".mp4"  # we got a video

        if not EXTRAS_ENABLED:
            msg = "video support"
            raise ExtrasNotEnabledError(msg)
    else:
        asset_content, suffix = None, None

    if suffix:
        asset_path = Path(ASSETS_ROOT) / (
            f"{
                get_asset_filename(
                    message_text, update.effective_message.date, context.user_data
                )
            }{suffix}"
        )
    else:
        asset_path = None

    return asset_path, asset_content


async def long_html_message(parts: list[str], bot: Bot) -> None:
    """Send a long HTML message in parts to avoid Telegram's message length limit."""
    current = ""
    for part in parts:
        if len(current) + len(part) > MAX_LENGTH:
            await bot.send_message(
                chat_id=CHAT_ID, text=current, parse_mode=ParseMode.HTML
            )
            current = ""
        current += part

    if current:
        if len(current) > MAX_LENGTH:
            current = current[: MAX_LENGTH - 100] + "\n\n[...truncated]"
        await bot.send_message(chat_id=CHAT_ID, text=current, parse_mode=ParseMode.HTML)
