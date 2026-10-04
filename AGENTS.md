# Project Guidelines

Telegram long-polling bot that turns a `title / === / tags / === / body` message into a Jekyll Markdown file committed through the GitHub Contents API. Setup, environment variables, and the message format are in [README.md](README.md).

## Architecture

First-party code is `tg_blog_updater/`:

- `__main__.py` — `python -m tg_blog_updater` entry
- `main.py` — handlers, GitHub commit, polling
- `posts.py` — message parsing and Jekyll rendering
- `utils.py` — `get_env()` for every config value

`get_repository()` builds the PyGithub client on first use and caches it. `main()` calls it before polling so a bad token fails at startup. Importing the package does not require credentials.

`handle_message` runs `create_post` with `asyncio.to_thread`, so GitHub I/O does not block the event loop. There is no local database; GitHub is the source of truth.

## Build and Test

Poetry keeps the virtualenv in-project (`poetry.toml`).

- `make dev` — install runtime, dev, and test groups
- `make install` — runtime dependencies only
- `make run` — `poetry run python -m tg_blog_updater`
- `make lint` — black, isort, flake8, and pylint (`.pylintrc`)
- `make test` — `poetry run pytest` (`testpaths = tests`)
- `make check` — lint and test

Do not add a dotenv loader; the process reads the environment, and Compose injects `.env`.

The production image installs the locked main dependencies into a virtualenv and runs `python -m tg_blog_updater` as a non-root user. [`.github/workflows/ci.yml`](.github/workflows/ci.yml) lints and tests. [`.github/workflows/release.yml`](.github/workflows/release.yml) publishes the image when a GitHub release is published.

## Conventions

- Read configuration only through `utils.get_env`. A missing or blank required key raises `MissingEnvironmentVariable`. Optional keys are `POST_PATH` (default `_posts`), `TIMEZONE` (default `Asia/Tehran`), and `TELEGRAM_BASE_URL`.
- Only the chat whose id equals `CHAT_ID` may create posts. Handler failures are reported to `DEBUG_CHAT_ID`.
- New posts are `{POST_PATH}/YYYY-MM-DD-{slug}.md`. The front-matter `date` uses `TIMEZONE`. A second post with the same date and slug raises `PostExistsError`.
- Tag front matter splits the tag segment on commas and quotes each tag.
- Never commit `.env` or tokens (`TELEGRAM_TOKEN`, `GITHUB_TOKEN`).
- Keep behavior changes inside `tg_blog_updater/` unless the task is packaging, Docker, or CI.
