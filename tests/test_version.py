# pylint: disable=missing-module-docstring,missing-function-docstring

from pathlib import Path

from tg_blog_updater import __version__


def test_package_version_matches_pyproject():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert f'version = "{__version__}"' in pyproject
