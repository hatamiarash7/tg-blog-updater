# pylint: disable=missing-module-docstring,missing-function-docstring

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from github import GithubException

from tg_blog_updater.main import (
    PostExistsError,
    create_post,
    error_handler,
    handle_message,
    start,
)


def _update(chat_id, text):
    message = AsyncMock()
    message.text = text
    message.chat_id = chat_id
    return SimpleNamespace(
        effective_message=message,
        effective_chat=SimpleNamespace(id=chat_id),
        effective_user=SimpleNamespace(first_name="Ada"),
    )


@pytest.fixture(autouse=True)
def _chat_id(monkeypatch):
    monkeypatch.setenv("CHAT_ID", "42")


@pytest.mark.asyncio
async def test_other_chats_cannot_create_posts():
    update = _update(7, "Title\n===\ntag\n===\nBody")

    await handle_message(update, AsyncMock())

    update.effective_message.reply_text.assert_awaited_once()
    assert "selected chats" in update.effective_message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_invalid_format_does_not_create_a_post(monkeypatch):
    created = MagicMock()
    monkeypatch.setattr("tg_blog_updater.main.create_post", created)
    update = _update(42, "hello")

    await handle_message(update, AsyncMock())

    created.assert_not_called()
    assert "Invalid message format" in (
        update.effective_message.reply_text.await_args.args[0]
    )


@pytest.mark.asyncio
async def test_valid_message_publishes_without_blocking_the_call(monkeypatch):
    created = {}

    def fake_create(title, tags, body):
        created["args"] = (title, tags, body)
        return "abc123"

    monkeypatch.setattr("tg_blog_updater.main.create_post", fake_create)
    update = _update(42, "Hello\n===\njekyll, telegram\n===\nBody text")

    await handle_message(update, AsyncMock())

    assert created["args"] == ("Hello", "jekyll, telegram", "Body text")
    update.effective_message.reply_text.assert_awaited_with(
        "Post created successfully!"
    )


@pytest.mark.asyncio
async def test_duplicate_post_gets_a_clear_reply(monkeypatch):
    def fake_create(title, tags, body):
        del title, tags, body
        raise PostExistsError("_posts/2026-10-03-hello.md")

    monkeypatch.setattr("tg_blog_updater.main.create_post", fake_create)
    update = _update(42, "Hello\n===\ntag\n===\nBody")

    await handle_message(update, AsyncMock())

    assert "already exists" in update.effective_message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_start_escapes_html_in_the_name():
    message = AsyncMock()
    message.chat_id = 42
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(first_name="<b>Ada</b>"),
    )
    context = AsyncMock()

    await start(update, context)

    text = context.bot.send_message.await_args.kwargs["text"]
    assert "&lt;b&gt;Ada&lt;/b&gt;" in text
    assert "<b>Ada</b>" not in text


@pytest.mark.asyncio
async def test_error_handler_truncates_before_sending(monkeypatch):
    monkeypatch.setenv("DEBUG_CHAT_ID", "99")
    context = AsyncMock()
    context.error = RuntimeError("x" * 10000)

    await error_handler("update", context)

    text = context.bot.send_message.await_args.kwargs["text"]
    assert len(text) <= 4096
    assert text.startswith("An exception was raised")


def test_create_post_commits_rendered_markdown(monkeypatch):
    now = datetime(2026, 10, 3, 15, 40, 1, tzinfo=ZoneInfo("Asia/Tehran"))
    repository = MagicMock()
    repository.create_file.return_value = {"commit": SimpleNamespace(sha="deadbeef")}
    monkeypatch.setattr("tg_blog_updater.main.get_repository", lambda: repository)
    monkeypatch.setattr("tg_blog_updater.main.posts.current_time", lambda: now)
    monkeypatch.setenv("POST_PATH", "_posts")

    sha = create_post("Hello World", "jekyll, telegram", "Body")

    assert sha == "deadbeef"
    path, message, content = repository.create_file.call_args.args
    assert path == "_posts/2026-10-03-hello-world.md"
    assert message == "Create new post: Hello World"
    assert "tags: " in content
    assert '"jekyll"' in content
    assert '"telegram"' in content


def test_create_post_maps_existing_file_to_post_exists(monkeypatch):
    repository = MagicMock()
    repository.create_file.side_effect = GithubException(
        422,
        {"message": 'Invalid request.\n\n"sha" wasn\'t supplied.'},
        None,
    )
    monkeypatch.setattr("tg_blog_updater.main.get_repository", lambda: repository)

    with pytest.raises(PostExistsError):
        create_post("Hello", "tag", "Body")
