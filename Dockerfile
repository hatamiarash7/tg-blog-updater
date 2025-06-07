FROM python:3.12-slim as builder

ARG APP_VERSION="undefined@docker"

ENV PYTHONDONTWRITEBYTECODE=true \
    PYTHONFAULTHANDLER=true \
    PYTHONUNBUFFERED=true \
    PYTHONHASHSEED=random \
    PYTHONPATH=/usr/lib/python3/dist-packages \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # poetry
    POETRY_NO_INTERACTION=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/poetry' \
    POETRY_HOME='/opt/poetry'

LABEL org.opencontainers.image.title="tg-blog-updater"
LABEL org.opencontainers.image.description="Update Jekyll blog using Telegram"
LABEL org.opencontainers.image.url="https://github.com/hatamiarash7/tg-blog-updater"
LABEL org.opencontainers.image.source="https://github.com/hatamiarash7/tg-blog-updater"
LABEL org.opencontainers.image.vendor="hatamiarash7"
LABEL org.opencontainers.image.author="hatamiarash7"
LABEL org.opencontainers.version="$APP_VERSION"
LABEL org.opencontainers.image.created="$DATE_CREATED"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt update \
    && apt install --no-install-recommends -y \
    curl \
    gcc \
    libffi-dev \
    libc6-dev \
    build-essential \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN ls && curl -sSL https://install.python-poetry.org | python3 - && sleep 5

ENV PATH="/opt/poetry/bin:$PATH"

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN poetry install --without dev,test --no-interaction --no-ansi

COPY . .

RUN mkdir proc

CMD ["python", "-m", "tg_blog_updater"]