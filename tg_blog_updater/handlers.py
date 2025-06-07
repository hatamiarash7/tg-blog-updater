"""Handles errors and user interactions for the Telegram bot."""

from __future__ import annotations

import contextlib
import html
import json
import traceback
from logging import Logger, getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.helpers import escape_markdown

from .github_client import commit_post
from .post_builder import create_post, parse_body_with_asset, parse_text_and_asset
from .tg_utils import get_asset, long_html_message
from .utils import get_env

logger: Logger = getLogger(__name__)

if TYPE_CHECKING:
    from telegram.ext import (
        ContextTypes,
    )

CHAT_ID = int(get_env("CHAT_ID"))
MAX_LEN = 4000


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Log the error and send a telegram message to notify the developer."""
    if context.error is None:
        logger.warning("No error information provided in context.")
        return

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
    message_list = [
        "An exception was raised while handling an update\n"
        f"""<pre>update = {
            html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))
        }</pre>\n\n""",
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n",
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n",
        f"<pre>{html.escape(tb_string)}</pre>",
    ]

    await long_html_message(message_list, context.bot)


async def handle_callback_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle button clicks for Keyboard actions."""
    query = update.callback_query
    if not query or not query.message or not context.user_data:
        logger.warning("Invalid callback query received, skipping.")
        return
    await query.answer()

    if query.data == "post":
        context.user_data["extend_mode"] = False
        context.user_data.pop("short_title", None)
        try:
            files = [
                (context.user_data["filepath"], context.user_data["post_content"])
            ] + context.user_data["asset_list"]
            if commit_post(
                files,
                f"Create new post: {Path(context.user_data['filepath']).name}",
            ):
                await query.edit_message_text(
                    "✅ Post has been published successfully!"
                )
            else:
                await query.edit_message_text("❌ Post data is missing.")
        except (KeyError, AttributeError, TypeError) as e:
            await query.edit_message_text(f"❌ An error occurred: {e!s}")

    if query.data == "cancel":
        context.user_data["extend_mode"] = False
        context.user_data.pop("short_title", None)
        await query.edit_message_text("❌ Post creation has been canceled.")

    if query.data == "extend":
        context.user_data["extend_mode"] = True
        await query.edit_message_text(
            "📎 Send a new message to continue creating your post."
        )

    if query.data == "edit":
        context.user_data["edit_mode"] = True
        context.user_data["extend_mode"] = False
        await query.edit_message_text("✏️ Please send the full, corrected post content.")
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=escape_markdown(context.user_data["post_content"], version=2),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_to_message_id=query.message.message_id,
        )


async def add_markup_keyboard(
    sent_message: Message, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Add a keyboard with action buttons to the message and remove the previous one."""
    if context.user_data is None:
        logger.error("No user data found in context.")
        return

    # Remove the previous keyboard if it exists
    if context.user_data.get("last_preview_id", None):
        with contextlib.suppress(BadRequest):
            await context.bot.edit_message_reply_markup(
                chat_id=CHAT_ID,
                message_id=context.user_data["last_preview_id"],
                reply_markup=None,
            )

    context.user_data["last_preview_id"] = sent_message.message_id

    # Define the keyboard with action buttons
    keyboard = [
        [
            InlineKeyboardButton("Post", callback_data="post"),
            InlineKeyboardButton("Cancel", callback_data="cancel"),
            InlineKeyboardButton("Extend", callback_data="extend"),
            InlineKeyboardButton("Edit", callback_data="edit"),
        ]
    ]

    await sent_message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and create a post."""
    if (
        not update.effective_chat
        or not update.effective_user
        or not update.message
        or not update.effective_message
        or context.user_data is None
    ):
        logger.warning("Invalid message received, skipping.")
        return

    if update.effective_chat.id != CHAT_ID:
        await update.message.reply_text(
            "This bot is only available to work in selected chats. Current ID :"
            + str(update.effective_chat.id)
        )
        return

    try:
        message_text: str = update.message.text or update.message.caption or ""

        asset_path, asset_content = await get_asset(
            update=update,
            context=context,
            logger=logger,
        )

        asset = (asset_path, asset_content) if asset_content else None

        if context.user_data.get("extend_mode", False):
            # If in extend mode, extend the existing parsed post and assets
            context.user_data["post_content"] += parse_body_with_asset(
                body=message_text,
                asset_path=asset_path,
            )
            if asset:
                context.user_data["asset_list"].append(asset)

        elif context.user_data.get("edit_mode", False):
            context.user_data["post_content"] = message_text

        else:  # extend mode == false && edit mode == false
            parsed_post = parse_text_and_asset(
                text=message_text,
                author_fallback=str(update.effective_user.username),
                asset_path=asset_path,
            )
            context.user_data["asset_list"] = (
                [(asset_path, asset_content)] if asset_path else []
            )
            context.user_data["filepath"], context.user_data["post_content"] = (
                create_post(parsed_post)
            )

        context.user_data["edit_mode"] = False

        # Send the preview with buttons
        sent_message = await update.message.reply_text(
            f"""Preview of your post:\n\n{
                escape_markdown(
                    context.user_data["post_content"]
                    + f"\n\nAssets:\n{
                        (
                            '\n'.join(
                                f'- {asset_path.name}'
                                for asset_path, _ in context.user_data['asset_list']
                            )
                            if context.user_data['asset_list']
                            else 'None'
                        )
                    }",
                    version=2,
                )
            }""",
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        await add_markup_keyboard(sent_message, context)

    except ValueError as err:
        await update.message.reply_text(str(err))
        return
