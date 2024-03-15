# Update Jekyll blog using Telegram

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![GitHub release](https://img.shields.io/github/release/hatamiarash7/tg-blog-updater.svg)](https://GitHub.com/hatamiarash7/tg-blog-updater/releases/) [![Release](https://github.com/hatamiarash7/tg-blog-updater/actions/workflows/release.yml/badge.svg)](https://github.com/hatamiarash7/tg-blog-updater/actions/workflows/release.yml) ![GitHub](https://img.shields.io/github/license/hatamiarash7/tg-blog-updater)

It's a simple Telegram bot to read messages and update a Jekyll blog.

1. Read messages from a Telegram group, channel or direct chat.
2. Parse the message and extract metadata and content.
3. Create a new post in the Jekyll blog using Github's API.
4. Deploy new changes using your CI/CD pipeline *(It is up to you to implement this)*.

## How to use it

1. Create a new bot using BotFather and get the token.
2. Create a new Github token with `repo` scope.
3. Run the bot using the following environment variables:
    - `TELEGRAM_TOKEN`: The token of your bot
    - `DEBUG_CHAT_ID`: A chat id to send debug messages (For example, you can get all errors in your private chat)
    - `GITHUB_TOKEN`: The token to access the Github API.
    - `GITHUB_REPO_NAME`: The name of the repository with the format `username/repo`.
    - `POST_PATH`: The target path to create the new post. For Jekyll blogs, it is `_posts`.

```bash
docker run -d --name jekyll-telegram-bot \
    -e TELEGRAM_TOKEN=your-telegram-token \
    -e DEBUG_CHAT_ID=your-chat-id \
    -e GITHUB_TOKEN=your-github-token \
    -e GITHUB_REPO_NAME=your-username/your-repo \
    -e POST_PATH=_posts \
    hatamiarash7/tg-blog-updater:1.0.0
```

## Message format

There is a default format to create a new post. The bot will parse the message and create a new post using the following format:

```text
title
===
tags ( comma separated )
===
content
```

For example:

```text
Hello world
===
jekyll,telegram,blog
===
This is the content of the post
```

> You should change the code if you want to use a different format.

---

## Support 💛

[![Donate with Bitcoin](https://img.shields.io/badge/Bitcoin-bc1qmmh6vt366yzjt3grjxjjqynrrxs3frun8gnxrz-orange)](https://donatebadges.ir/donate/Bitcoin/bc1qmmh6vt366yzjt3grjxjjqynrrxs3frun8gnxrz) [![Donate with Ethereum](https://img.shields.io/badge/Ethereum-0x0831bD72Ea8904B38Be9D6185Da2f930d6078094-blueviolet)](https://donatebadges.ir/donate/Ethereum/0x0831bD72Ea8904B38Be9D6185Da2f930d6078094)

<div><a href="https://payping.ir/@hatamiarash7"><img src="https://cdn.payping.ir/statics/Payping-logo/Trust/blue.svg" height="128" width="128"></a></div>

## Contributing 🤝

Don't be shy and reach out to us if you want to contribute 😉

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request

## Issues

Each project may have many problems. Contributing to the better development of this project by reporting them. 👍
