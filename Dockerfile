# -- Builder stage --
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc pkg-config libmariadb-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --extra postgres --extra mysql

# -- Final stage --
FROM python:3.14-slim

LABEL org.opencontainers.image.source="https://github.com/KrzysztofHajdamowicz/bash.org-like"
LABEL org.opencontainers.image.description="A bash.org-like quote database built with Django"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update && \
    apt-get install -y --no-install-recommends libmariadb3 libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

RUN addgroup --system app && adduser --system --ingroup app app && \
    mkdir -p /app/data && chown -R app:app /app

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "BashOrgLike.wsgi:application", "--bind", "0.0.0.0:8000"]
