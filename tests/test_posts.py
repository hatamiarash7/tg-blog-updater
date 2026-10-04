# pylint: disable=missing-module-docstring,missing-function-docstring

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from tg_blog_updater import posts
from tg_blog_updater.utils import MissingEnvironmentVariable

TEHRAN = ZoneInfo("Asia/Tehran")
NOW = datetime(2026, 10, 3, 15, 40, 1, tzinfo=TEHRAN)


def test_parse_message_splits_comma_separated_tags():
    parsed = posts.parse_message(
        "Hello world\n===\njekyll, telegram, blog\n===\nThis is the content"
    )

    assert parsed == ("Hello world", "jekyll, telegram, blog", "This is the content")


def test_parse_message_accepts_crlf_and_spaces_around_separator():
    parsed = posts.parse_message("Title\r\n === \r\ntags\r\n===\r\nBody line")

    assert parsed == ("Title", "tags", "Body line")


def test_parse_message_keeps_multiline_body():
    parsed = posts.parse_message("Title\n===\ntag\n===\nLine one\n\nLine two")

    assert parsed == ("Title", "tag", "Line one\n\nLine two")


@pytest.mark.parametrize(
    "text",
    [
        "",
        "only a title",
        "Title\n===\n\n===\nBody",
        "Title\n===\n,,,\n===\nBody",
        "Title\n===\ntags\n===\n   ",
        "\n===\ntags\n===\nBody",
    ],
)
def test_parse_message_rejects_invalid_shapes(text):
    assert posts.parse_message(text) is None


def test_unicode_title_is_kept_in_the_filename():
    path = posts.build_file_path("سلام دنیا", NOW, "_posts")

    assert path == "_posts/2026-10-03-سلام-دنیا.md"


def test_punctuation_only_title_gets_a_fallback_slug():
    path = posts.build_file_path("!!!", NOW, "/_posts/")

    assert path == "_posts/2026-10-03-post.md"


def test_render_post_quotes_yaml_and_uses_timezone_offset():
    content = posts.render_post('Hello: "world"', "open-source, jekyll", "Body", NOW)

    assert content == (
        "---\n"
        'title: "Hello: \\"world\\""\n'
        "date: 2026-10-03 15:40:01 +0330\n"
        'tags: ["open-source", "jekyll"]\n'
        "---\n\n"
        "Body\n"
    )


def test_blog_timezone_defaults_to_tehran(monkeypatch):
    monkeypatch.delenv("TIMEZONE", raising=False)

    assert posts.blog_timezone() == TEHRAN


def test_blog_timezone_rejects_unknown_names(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "Not/AZone")

    with pytest.raises(MissingEnvironmentVariable):
        posts.blog_timezone()
