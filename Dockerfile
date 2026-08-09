# syntax=docker/dockerfile:1.6

FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv


FROM base AS deps

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project


FROM base AS runtime

COPY --from=deps /usr/local /usr/local

COPY src/ /app/

CMD ["python", "main.py"]