# Update Jekyll blog using Telegram

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![GitHub release](https://img.shields.io/github/release/hatamiarash7/tg-blog-updater.svg)](https://GitHub.com/hatamiarash7/tg-blog-updater/releases/) [![Release](https://github.com/hatamiarash7/tg-blog-updater/actions/workflows/release.yml/badge.svg)](https://github.com/hatamiarash7/tg-blog-updater/actions/workflows/release.yml) ![GitHub](https://img.shields.io/github/license/hatamiarash7/tg-blog-updater)

A Telegram bot that turns a chat message into a Jekyll Markdown post and commits it with the GitHub Contents API. Deploying the site after that commit is up to your own pipeline.

1. Read a message from the configured Telegram chat.
2. Parse the title, tags, and body.
3. Create `_posts/YYYY-MM-DD-title.md` in the GitHub repository.

## Requirements

- A bot token from [BotFather](https://t.me/BotFather).
- The numeric id of the chat that is allowed to publish. In a group, disable privacy mode or make the bot an admin so it can read messages. In a channel, add the bot as an admin.
- A GitHub token that can write file contents in the target repository. A fine-grained token with **Contents: Read and write** on that repo is enough. Classic tokens need the `repo` scope.
- `DEBUG_CHAT_ID` is a chat where the bot can post tracebacks. A private chat with the bot works.

## Configuration

Copy [`.env.example`](.env.example) to `.env`. Compose reads that file. The process itself does not load dotenv files.

| Variable            | Required | Description                                                             |
| ------------------- | -------- | ----------------------------------------------------------------------- |
| `TELEGRAM_TOKEN`    | yes      | Bot token from BotFather                                                |
| `CHAT_ID`           | yes      | Numeric chat id allowed to create posts                                 |
| `DEBUG_CHAT_ID`     | yes      | Numeric chat id that receives errors                                    |
| `GITHUB_TOKEN`      | yes      | Token with contents write access                                        |
| `GITHUB_REPO_NAME`  | yes      | Repository, as `username/repo`                                          |
| `POST_PATH`         | no       | Directory for new posts. Defaults to `_posts`                           |
| `TIMEZONE`          | no       | IANA timezone for the post date and filename. Defaults to `Asia/Tehran` |
| `TELEGRAM_BASE_URL` | no       | Bot API base URL. Defaults to `https://api.telegram.org/bot`            |

The front-matter `date` uses this timezone. With the default, the offset is `+0330`.

## Run with Docker

```bash
docker run -d --name tg-blog-updater --init --env-file .env \
    --restart unless-stopped \
    hatamiarash7/tg-blog-updater:latest
```

Release tags are published as `hatamiarash7/tg-blog-updater:vX.Y.Z` alongside `latest`.

Compose builds the same image and restarts it unless you stop it:

```bash
docker compose up -d --build
```

The image runs as a non-root user. Publishing a GitHub release builds a multi-arch image for `linux/amd64`, `linux/386`, `linux/arm64`, and `linux/arm/v7`.

## Message format

Send `/start` for the same layout. Title and tags are one line each. Tags are comma-separated. The body can span multiple lines.

```text
title
===
tags (comma separated)
===
content
```

```text
Hello world
===
jekyll, telegram, blog
===
This is the content of the post
```

That message becomes a file like `_posts/2026-10-03-hello-world.md`:

```markdown
---
title: "Hello world"
date: 2026-10-03 15:40:01 +0330
tags: ["jekyll", "telegram", "blog"]
---

This is the content of the post
```

A second post with the same date and slug is rejected, and the bot asks you to change the title. Titles in other languages are kept in the filename.

## Development

Poetry keeps the virtualenv in the project (`.venv`).

```bash
make dev    # runtime, dev, and test dependencies
make run    # python -m tg_blog_updater
make check  # format check, flake8, pylint, and pytest
make format # black and isort
```

`make help` lists every target.

## Support

[![Donate with Bitcoin](https://img.shields.io/badge/Bitcoin-bc1qmmh6vt366yzjt3grjxjjqynrrxs3frun8gnxrz-orange)](https://donatebadges.ir/donate/Bitcoin/bc1qmmh6vt366yzjt3grjxjjqynrrxs3frun8gnxrz) [![Donate with Ethereum](https://img.shields.io/badge/Ethereum-0x0831bD72Ea8904B38Be9D6185Da2f930d6078094-blueviolet)](https://donatebadges.ir/donate/Ethereum/0x0831bD72Ea8904B38Be9D6185Da2f930d6078094)

<div><a href="https://payping.ir/@hatamiarash7"><img src="https://cdn.payping.ir/statics/Payping-logo/Trust/blue.svg" height="128" width="128" alt="PayPing"></a></div>

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b my-new-feature`
3. Run `make check` before opening a pull request.

## Issues

Bug reports and pull requests are welcome.
