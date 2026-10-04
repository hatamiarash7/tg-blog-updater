"""Parse a Telegram message into a Jekyll post."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from slugify import slugify

from tg_blog_updater import utils

_MESSAGE_PATTERN = re.compile(
    r"^([^\n]+)\n[ \t]*===[ \t]*\n([^\n]+)\n[ \t]*===[ \t]*\n(.+)\Z",
    re.DOTALL,
)


def blog_timezone() -> ZoneInfo:
    """Return the timezone used for the post date and filename."""

    name = utils.get_env("TIMEZONE", "Asia/Tehran")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise utils.MissingEnvironmentVariable(
            f"Environment variable TIMEZONE is not a valid IANA timezone: {name}"
        ) from exc


def current_time() -> datetime:
    """Current time in the configured blog timezone."""

    return datetime.now(blog_timezone())


def parse_message(text: str) -> tuple[str, str, str] | None:
    """Split a message into title, tags, and body.

    Title and tags are single lines. Tags are comma-separated. Returns None
    when the message does not match the format or a section is empty.
    """

    normalized = text.replace("\r\n", "\n").strip()
    match = _MESSAGE_PATTERN.fullmatch(normalized)
    if match is None:
        return None

    title, tags, body = (part.strip() for part in match.groups())
    if not title or not tags or not body:
        return None
    if not _tag_list(tags):
        return None
    return title, tags, body


def build_file_path(title: str, now: datetime, post_path: str) -> str:
    """Jekyll post path ``{post_path}/YYYY-MM-DD-{slug}.md``."""

    slug = slugify(title, lowercase=True, allow_unicode=True) or "post"
    directory = post_path.strip("/") or "_posts"
    return f"{directory}/{now.strftime('%Y-%m-%d')}-{slug}.md"


def render_post(title: str, tags: str, body: str, now: datetime) -> str:
    """Jekyll markdown, including YAML front matter."""

    quoted_tags = ", ".join(_yaml_double_quoted(tag) for tag in _tag_list(tags))
    return (
        "---\n"
        f"title: {_yaml_double_quoted(title)}\n"
        f"date: {now.strftime('%Y-%m-%d %H:%M:%S %z')}\n"
        f"tags: [{quoted_tags}]\n"
        "---\n\n"
        f"{body.strip()}\n"
    )


def _tag_list(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def _yaml_double_quoted(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
