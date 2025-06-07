"""Module to parse and create blog posts from Telegram messages."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from slugify import slugify

from .utils import (
    choose_destination_folder,
    get_env,
    link_preview,
    youtube_embed,
)

ASSETS_ROOT = Path(get_env("ASSETS_PATH", "assets"))


class ParsedPost(TypedDict):
    """Structured data for a blog post."""

    title: str
    categories: str | None
    tags: str | None
    folder: str
    author: str
    layout: str
    body: str


def split_message(message: str) -> tuple[str, str, str]:
    """Split the incoming message into 3 parts: title - meta-block - body.

    Delimiters are any line made only of '=' characters.

    Returns:
        tuple[str, str, str]: title, meta_block, body

    Raises:
        ValueError: If the message format is invalid.

    """
    try:
        title, meta_block, body = re.split(r"\n=+\n", message, maxsplit=2)
        return title.strip(), meta_block.strip(), body.strip()
    except Exception as exc:
        msg = (
            "Invalid format. Use:\n"
            "Title\n===\n+category #tag &layout @author /filepath\n===\nContent"
        )
        raise ValueError(msg) from exc


def parse_meta(
    meta_block: str,
    symbol: str,
    extra_chars: str = "",
) -> list[str] | None:
    """Turn the lines in the meta-block into structured data.

    Returns:
        A sorted list of strings found in the meta-block matching the symbol,
        or None if none found.

    """
    base_chars = "-a-zA-Z0-9_"
    valid_chars = base_chars + re.escape(extra_chars)
    pattern = re.compile(re.escape(symbol) + rf"([{valid_chars}]+)")
    return sorted(set(pattern.findall(meta_block)))


def parse_body_with_asset(body: str, asset_path: Path | None) -> str:
    """Parse the body of the post, including assets and YouTube links.

    Args:
        body: The body text of the post.
        asset_path: An optional asset to include in the body.
        prev_text: Text to prepend to the body, if any.

    Returns:
        str: The processed body text with assets and YouTube links formatted.

    """
    body = link_preview(youtube_embed(body))  # turn URLs → `{% youtube … %}` & links

    if asset_path and ".webp" in asset_path.name:
        body += f"\n\n![{asset_path.name}]({asset_path})\n"
    elif asset_path and ".mp4" in asset_path.name:
        body += "\n\n{% video " + asset_path.name + " %}\n"

    return "\n" + body.strip() + "\n"


def parse_text_and_asset(
    text: str,
    author_fallback: str,
    asset_path: Path | None = None,
) -> ParsedPost:
    """Parse the text and assets to create a post structure.

    Args:
        text: The full text of the post, including title, metadata and body.
        author_fallback: Fallback author name if not specified in the text.
        asset_path: An optional asset to include in the body.

    Returns:
        A dictionary with the post structure containing title, categories, tags, folder,
        author, and body.

    """
    title, meta_block, body = split_message(text)

    categories = parse_meta(meta_block, "+")

    tags = parse_meta(meta_block, "#")

    author = parse_meta(meta_block, "@")
    if author is None:
        author = [author_fallback]

    layout = parse_meta(meta_block, "&", extra_chars="/")

    base_path = parse_meta(meta_block, "/", extra_chars="/")
    base_path = base_path[0] if base_path else None

    body = parse_body_with_asset(body, asset_path)

    return {
        "title": title,
        "categories": ", ".join(categories) if categories else None,
        "tags": ", ".join(tags) if tags else None,
        "folder": base_path or choose_destination_folder(categories),
        "author": ", ".join(author),
        "body": body,
        "layout": layout[0] if layout else get_env("POST_LAYOUT", "post"),
    }


def create_post(
    parsed_post: ParsedPost,
) -> tuple[Path, str]:
    """Create a post file from the parsed post data.

    Returns:
        tuple[Path, str]: The file path and the content of the post in Markdown format.

    """
    now = datetime.now().astimezone()
    offset = now.strftime("%z")  # Ej: '+0200'
    offset_formatted = f"{offset[:3]}:{offset[3:]}"  # Ej: '+02:00'
    filename = f"{now:%Y-%m-%d}-{slugify(parsed_post['title'])}.md"
    file_path = Path(parsed_post["folder"]) / filename

    front = ["---", f"title: {parsed_post['title']}"]

    if parsed_post["categories"]:
        front.append(f"categories: {parsed_post['categories']}")

    if parsed_post["tags"]:
        front.append(f"tags: {parsed_post['tags']}")

    front.append(f"author: {parsed_post['author']}")

    front.extend([
        f"layout: {parsed_post['layout']}",
        f"date: {now:%Y-%m-%d %H:%M:%S} {offset_formatted}",
        "---",
        "",
    ])

    return file_path, "\n".join(front) + parsed_post["body"].strip() + "\n"
