# Project Guidelines

Telegram long-polling bot that turns a `title / === / tags / === / body` message into a Jekyll Markdown file committed through the GitHub Contents API. Setup, environment variables, and the message format are in [README.md](README.md).

## Architecture

First-party code is only `tg_blog_updater/`:

- `__main__.py` — `python -m tg_blog_updater` entry
- `main.py` — handlers, post creation, polling
- `utils.py` — `get_env()` for every config value

`main.py` builds the PyGithub client and calls `get_repo()` at import time. `GITHUB_TOKEN` and `GITHUB_REPO_NAME` must be set before that module is imported, including from tests.

`handle_message` is async and calls synchronous `create_post`, so GitHub I/O runs on the event loop. There is no local database; GitHub is the source of truth.

## Build and Test

Poetry keeps the virtualenv in-project (`poetry.toml`).

- `make dev` — install runtime, dev, and test groups
- `make run` — `poetry run python -m tg_blog_updater`
- `make lint` — pylint with `.pylintrc` (the only lint target)
- `make test` — `poetry run pytest` (`testpaths = tests`; no `tests/` tree yet)

Black, isort, and flake8 are dev dependencies and are not Makefile targets. Do not add a dotenv loader; the process reads the environment, and Compose injects `.env`.

The production image runs `poetry install --without dev,test` and `python -m tg_blog_updater`. [`.github/workflows/release.yml`](.github/workflows/release.yml) publishes that image and does not run lint or tests.

## Conventions

- Read configuration only through `utils.get_env`. A missing required key raises `Exception`. Optional keys today are `POST_PATH` (default `_posts`) and `TELEGRAM_BASE_URL`.
- Only the chat whose id equals `CHAT_ID` may create posts. Handler failures are reported to `DEBUG_CHAT_ID`.
- New posts are `{POST_PATH}/YYYY-MM-DD-{slug}.md`. Front-matter `date` uses a hardcoded `+3:30` offset. A second post with the same date and slug fails in `repo.create_file`.
- Tag front matter splits the tag segment on `-` (`tags.split("-")`). That does not match the comma-separated example in the README. Change it only when the task is the tag format.
- Never commit `.env` or tokens (`TELEGRAM_TOKEN`, `GITHUB_TOKEN`).
- Keep behavior changes inside `tg_blog_updater/` unless the task is packaging, Docker, or CI.
