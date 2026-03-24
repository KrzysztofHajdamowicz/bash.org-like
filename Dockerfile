# -- Builder stage --
FROM python:3.14-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc pkg-config libmariadb-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -- Final stage --
FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libmariadb3 libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local

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
