# pylint: disable=missing-module-docstring,missing-function-docstring

import pytest

from tg_blog_updater.utils import MissingEnvironmentVariable, get_env


def test_get_env_strips_whitespace(monkeypatch):
    monkeypatch.setenv("POST_PATH", "  blog/_posts  ")

    assert get_env("POST_PATH", "_posts") == "blog/_posts"


def test_get_env_returns_default_when_missing(monkeypatch):
    monkeypatch.delenv("POST_PATH", raising=False)

    assert get_env("POST_PATH", "_posts") == "_posts"


def test_get_env_returns_empty_default(monkeypatch):
    monkeypatch.delenv("OPTIONAL_EMPTY", raising=False)

    assert get_env("OPTIONAL_EMPTY", "") == ""


@pytest.mark.parametrize("value", [None, "", "   "])
def test_get_env_rejects_missing_or_blank_values(monkeypatch, value):
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    if value is not None:
        monkeypatch.setenv("TELEGRAM_TOKEN", value)

    with pytest.raises(MissingEnvironmentVariable):
        get_env("TELEGRAM_TOKEN")
