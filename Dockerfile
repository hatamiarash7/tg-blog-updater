# syntax=docker/dockerfile:1

FROM python:3.14.8-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.5.1

WORKDIR /app

RUN pip install --no-cache-dir \
    "poetry==${POETRY_VERSION}" \
    "poetry-plugin-export==1.10.1"

COPY pyproject.toml poetry.lock README.md ./
COPY tg_blog_updater ./tg_blog_updater

RUN poetry export \
    --only main \
    --format requirements.txt \
    --output requirements.txt \
    --without-hashes \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && poetry build --format wheel \
    && /opt/venv/bin/pip install --no-cache-dir --no-deps dist/*.whl

FROM python:3.14.8-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir /app \
    && chown app:app /app

COPY --from=builder --chown=app:app /opt/venv /opt/venv

WORKDIR /app
USER app

ARG APP_VERSION=dev
ARG DATE_CREATED=unknown

LABEL org.opencontainers.image.title="tg-blog-updater" \
    org.opencontainers.image.description="Update a Jekyll blog from Telegram messages" \
    org.opencontainers.image.url="https://github.com/hatamiarash7/tg-blog-updater" \
    org.opencontainers.image.source="https://github.com/hatamiarash7/tg-blog-updater" \
    org.opencontainers.image.vendor="hatamiarash7" \
    org.opencontainers.image.authors="hatamiarash7" \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.created="${DATE_CREATED}" \
    org.opencontainers.image.licenses="MIT"

CMD ["python", "-m", "tg_blog_updater"]
