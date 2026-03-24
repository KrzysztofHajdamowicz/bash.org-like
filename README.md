# bash.org-like

A self-hosted [bash.org](http://bash.org)-style quote database built with **Django 6.0** and **Python 3.14**. Users submit IRC/chat quotes, moderators approve or reject them, and anyone can upvote or downvote.

## Quick start

### With Docker (recommended)

```bash
# SQLite (simplest)
docker compose --profile sqlite up --build

# PostgreSQL
docker compose --profile postgres up --build

# MariaDB
docker compose --profile mariadb up --build
```

The app will be available at `http://localhost:8000/`.

### Local development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14+.

```bash
git clone https://github.com/KrzysztofHajdamowicz/bash.org-like.git
cd bash.org-like
uv sync
SECRET_KEY=dev DEBUG=True uv run python manage.py migrate
SECRET_KEY=dev DEBUG=True uv run python manage.py runserver
```

Create a superuser for the moderation panel:

```bash
SECRET_KEY=dev DEBUG=True uv run python manage.py createsuperuser
```

### Database drivers

SQLite works out of the box. For other databases, install the optional extras:

```bash
uv sync --extra postgres          # PostgreSQL
uv sync --extra mysql             # MariaDB/MySQL
```

Set `DATABASE_URL` to point to your database (parsed by [dj-database-url](https://github.com/jazzband/dj-database-url)).

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | Hard-coded fallback (override in production!) |
| `DEBUG` | Enable debug mode (`true`/`1`/`yes`) | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `*` |
| `DATABASE_URL` | Database connection URL | `sqlite:///db.sqlite3` |

## Running tests

```bash
SECRET_KEY=test DEBUG=True uv run --group dev pytest -v
```

96 tests with coverage reporting (85% threshold enforced).

## Linting

```bash
uv run --group dev ruff check . && uv run --group dev ruff format --check .
```

## Tech stack

- **Django 6.0.3** with function-based views
- **Bootstrap 5.3** frontend with vanilla JS for AJAX voting
- **WhiteNoise** for static file serving
- **Gunicorn** for production serving
- **uv** for dependency management
- **pytest** + **pytest-cov** for testing
- **ruff** for linting and formatting

## CI/CD

- **GitHub Actions**: lint, test, Docker build on every push/PR
- **CodeQL**: weekly security scanning
- **Dependabot**: automated dependency updates for Python, Docker, and GitHub Actions
- **GHCR publishing**: Docker images with SBOM generation and Sigstore attestations
