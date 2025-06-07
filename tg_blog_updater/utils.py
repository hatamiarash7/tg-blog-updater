"""Module providing helpers for the Telegram blog updater."""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests

EXTRAS_ENABLED = os.getenv("EXTRAS_ENABLED", "false").lower() in {"true", "1", "yes"}


class MissingEnvironmentVariableError(Exception):
    """Raised when a required environment variable is not defined."""


class ExtrasNotEnabledError(Exception):
    """Raised when an extra feature is not enabled in the configuration."""

    def __init__(self, feature: str) -> None:
        """Initialize the error with the feature name."""
        super().__init__(f"Feature '{feature}' is not enabled in the configuration.")
        self.feature = feature


def get_env(key: str, default: str | None = None) -> str:
    """Get environment variable.

    Args:
        key (str): Environment variable name
        default (str, optional): Default value if not found. Defaults to None.

    Returns:
        str: Environment variable value

    Raises:
        MissingEnvironmentVariableError: If the environment variable is not set
        and no default is provided.

    """
    if key in os.environ:
        return os.environ[key]
    if default is not None:
        return default
    msg = f"Environment variable '{key}' is not set."
    raise MissingEnvironmentVariableError(msg)


YOUTUBE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:youtube\.com/watch\?v=|youtu\.be/)"
    r"([\w\-]{11})"
)


def youtube_embed(text: str) -> str:
    """Replace every YouTube URL with `{% youtube ID %}`.

    Returns:
        str: The original text with YouTube URLs replaced by Liquid embed tags.

    """
    if not EXTRAS_ENABLED:
        return text
    return YOUTUBE_RE.sub(r"{% youtube \1 %}", text)


URL_RE = re.compile(r"https?://[^\s)]+")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def link_preview(text: str) -> str:
    """Replace URLs in the text with a simple link preview.

    Returns:
        str: The original text with URLs replaced by formatted link previews.

    """

    def replace(match: re.Match[str]) -> str:
        url = match.group(0)
        try:
            r = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            title_match = TITLE_RE.search(r.text)
            title: str = title_match.group(1).strip() if title_match else url
        except requests.RequestException:
            title = url
        return f"[🌐 {title}]({url})"

    return URL_RE.sub(replace, text)


def choose_destination_folder(categories: list[str] | None) -> str:
    """Decide which folder to drop the file in.

    Returns:
        str: The path to the folder where the post should be saved.

    """
    if categories:
        for category in categories:
            folder_path = Path("/" + category + "/_posts")
            if folder_path.is_dir():
                return str(folder_path)
    return get_env("POST_PATH", "_posts")
