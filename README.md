# Update Jekyll blog using Telegram

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![GitHub release](https://img.shields.io/github/release/hatamiarash7/tg-blog-updater.svg)](https://GitHub.com/hatamiarash7/tg-blog-updater/releases/) [![Release](https://github.com/hatamiarash7/tg-blog-updater/actions/workflows/release.yml/badge.svg)](https://github.com/hatamiarash7/tg-blog-updater/actions/workflows/release.yml) ![GitHub](https://img.shields.io/github/license/hatamiarash7/tg-blog-updater)

It's a simple Telegram bot to read messages and update a Jekyll blog.

1. Read messages from a Telegram group, channel or direct chat.
2. Parse the message:
    - extract metadata and content
    - **photo and video[*](#ci-cd-pipeline)** support.
    - **Youtube[*](#ci-cd-pipeline)** video support.
    - link embedding.
3. Create a new post in the Jekyll blog using Github's API.
4. Deploy new changes using your CI/CD pipeline.

## How to use it

1. Create a new bot using BotFather and get the token.
2. Create a new Github token with `repo` scope.
3. For Youtube and .mp4 video support, you need a [CI/CD pipeline](#ci-cd-pipeline).
4. Run the bot using the following environment variables:
    - `TELEGRAM_TOKEN`: The token of your bot
    - `CHAT_ID`: A chat id that the bot should listen to. It can be a group, channel or a direct chat.
    - `DEBUG_CHAT_ID`: A chat id to send debug messages (For example, you can get all errors in your private chat)
    - `GITHUB_TOKEN`: The token to access the Github API.
    - `GITHUB_REPO_NAME`: The name of the repository with the format `username/repo`.
    - `POST_PATH`: The target path to create the new post. For Jekyll blogs, it is `_posts`.
    - `POST_LAYOUT`: A fallback layout for the post. If you don't specify it, the bot will use `post` as the default layout.
    - `EXTRAS_ENABLED`: Boolean value to enable extra features. This requires a [CI/CD pipeline](#ci-cd-pipeline) to deploy the changes. Default is `false`:
        - `youtube`: Enable Youtube video support.
        - `video`: Enable video support.

> [!TIP]
> You can use `TELEGRAM_BASE_URL` environment variable to change the base URL of the Telegram API.

```bash
docker run -d --name jekyll-telegram-bot \
    -e TELEGRAM_TOKEN=your-telegram-token \
    -e CHAT_ID=your-chat-id \
    -e DEBUG_CHAT_ID=your-chat-id \
    -e GITHUB_TOKEN=your-github-token \
    -e GITHUB_REPO_NAME=your-username/your-repo \
    -e POST_PATH=_posts \
    -e POST_LAYOUT=post \
    -e EXTRAS_ENABLED=true \
    hatamiarash7/tg-blog-updater:v1.0.1
```

## CI CD Pipeline

To enable video support and other extra features, you need to set up a CI/CD pipeline (like Github Actions or Gitlab CI) to deploy the changes.

### Setting up Github Actions

Follow this guide to setup a [custom Github Actions workflow in your Repo](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow)

You can use the provided [`gh-actions.yml`](extras/gh-actions.yml) file in [`/extras`](extras/): copy it to the `.github/workflows` directory of your Jekyll blog, and if needed, customize it according to your needs.

### Plugin Support

Copy the .rb files in [`/extras`](extras/) to the `_plugins` directory of your Jekyll blog.

**Note**: You need to add the option `safe: false` to your `_config.yml` file to enable the plugins.

## Message format

There is a default format to create a new post. The bot will parse the message and create a new post using the following format:

```text
title
===
#tag1 #tag2 #tag3
+category1 +category2
@author1 @author2 (default: Telegram Username)
&layout (default: POST_LAYOUT)
/path/where/post/should/be/saved/title.md (default: path/to/category/title.md OR POST_PATH/title.md)
===
content
```

For example:

```text
Hello world
===
#jekyll #telegram #blog
+programming +python
@hatamiarash7
&post
/posts/2023-10-01-hello-world.md
===
This is the content of the post
```

> [!NOTE]
> You should change the code if you want to use a different format.

---

## User Commands

After sending a valid message, you can use the following commands:

- `POST`: Post the actual message to the blog.
- `CANCEL`: Cancel the post creation.
- `EXTEND`: Extend the post creation to add more content.
- `EDIT`: Edit the post content.

## Limitations

- The bot cannot handle Gallery posts or multiple images in a single post. Separate each image in a new message.
- The bot cannot handle messages with more than 4096 characters, which is the maximum length of a Telegram message.

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
