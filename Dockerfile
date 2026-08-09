FROM python:3.13-slim AS deps

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --system


FROM python:3.13-slim AS runtime

WORKDIR /app

COPY --from=deps /usr/local /usr/local
COPY src/ /app/

CMD ["python", "main.py"]