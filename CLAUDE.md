# CLAUDE.md — bash.org-like

## Project overview

A **bash.org-like quote database** built with Django. Users submit IRC/chat-style quotes, moderators approve or reject them, and anyone can upvote/downvote approved quotes. Think bash.org but self-hosted.

- **Django 6.0.3** on **Python 3.12+**
- Single Django app: `quotes`
- Function-based views (no CBVs)
- SQLite by default, PostgreSQL and MariaDB via `DATABASE_URL`
- Bootstrap 5.3 frontend with vanilla JS for AJAX voting

## Quick commands

```bash
# Install dependencies (core only — SQLite works out of the box)
uv sync

# Install with database drivers
uv sync --extra postgres          # PostgreSQL
uv sync --extra mysql             # MariaDB/MySQL
uv sync --extra postgres --extra mysql  # both

# Run dev server (set env vars or use defaults)
SECRET_KEY=dev DEBUG=True uv run python manage.py runserver

# Run tests (96 tests) — pytest with coverage and JUnit XML for CI reporting
SECRET_KEY=test DEBUG=True uv run --group dev pytest -v

# Or via Django's test runner (still works)
SECRET_KEY=test DEBUG=True uv run python manage.py test

# Lint
uv run --group dev ruff check . && uv run --group dev ruff format --check .

# Generate migrations after model changes
SECRET_KEY=test uv run python manage.py makemigrations

# Docker (pick a profile: sqlite, postgres, mariadb)
docker compose --profile sqlite up --build
```

## Project structure

```
BashOrgLike/             # Django project package
  settings.py            # All config — env-driven (SECRET_KEY, DEBUG, DATABASE_URL, ALLOWED_HOSTS)
  context_processors.py  # Custom context processor (site_name)
  urls.py                # Root URL conf — admin + includes quotes.urls
  wsgi.py                # WSGI entry point for gunicorn

quotes/                  # The single Django app
  models.py              # Quote model (the only model)
  views.py               # 16 function-based views (including _paginate helper)
  urls.py                # 15 URL patterns, all using path()
  forms.py               # AddQuoteForm (ModelForm with honeypot field)
  tests.py               # 96 tests across 15 test classes
  admin.py               # Quote registered in Django admin
  apps.py                # QuotesConfig
  templatetags/
    quote_extras.py      # Custom `sub` filter (karma = votes_up - votes_down)
  templates/quotes/
    base.html            # Bootstrap 5 layout, navbar, static assets
    welcome.html         # Home page
    quotes_list.html     # Paginated quote list (accepted + best + trash views share this)
    quotes_view.html     # Single quote detail with vote forms
    quote_add.html       # Submit new quote form
    quote_added.html     # Success page after submission
    quotes_manage.html   # Moderation panel (login required)
    login_form.html      # Login page
    paginator.html       # Reusable pagination partial

icons/                   # Favicons and PWA manifest (served as static files)

pyproject.toml           # Project metadata, dependencies, and ruff config (PEP 621)
uv.lock                  # Reproducible lock file (committed to git)
```

## Architecture and design

### Package management — uv

This project uses **[uv](https://docs.astral.sh/uv/)** instead of pip:
- **`pyproject.toml`** — single source of truth for dependencies (PEP 621 standard)
- **`uv.lock`** — deterministic lock file with hashes, committed to git
- **Optional extras** — database drivers are optional: `postgres` (psycopg3) and `mysql` (mysqlclient). Core deps (Django, gunicorn, whitenoise, dj-database-url) are always installed.
- **Dev dependency group** — `ruff`, `pytest`, `pytest-django`, and `pytest-cov` are in `[dependency-groups] dev`, installed with `--group dev`
- **No `requirements.txt`** — replaced by pyproject.toml + uv.lock

### The Quote model

The only model. Status uses a `models.IntegerChoices` enum:

```python
class Quote(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 1, "Is pending"
        REJECTED = 2, "Is rejected"
        APPROVED = 3, "Is approved"
```

Always use the enum (e.g. `Quote.Status.APPROVED`) rather than bare integers when querying or setting status.

Key fields:
- `content` — the quote text (TextField)
- `votes_up` / `votes_down` — separate counters (PositiveIntegerField), not a net score
- `acceptant` — ForeignKey to `settings.AUTH_USER_MODEL` (SET_NULL), the moderator who approved/rejected
- `created_date` — auto_now_add, used for default ordering
- `status` — IntegerField with `Status.choices`, defaults to `Status.PENDING`, has `db_index=True`

`DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'` — the pk is a BigAutoField.

### Views pattern

All views are plain functions. The codebase does **not** use class-based views.

`site_name` is injected globally via a custom context processor (`BashOrgLike.context_processors.site_name`). Every `render()` call passes `active_nav` (a string identifying the active nav tab). This string drives the active state in the navbar via `{% if active_nav == 'accepted_list' %}`.

Auth-protected views use `@login_required(login_url='/login/')`. There is no LoginRequiredMiddleware — most pages are public.

**State-changing operations** (accept, reject, delete, vote) use `@require_POST` and POST forms with CSRF tokens. Templates use `<form method="post">` with `{% csrf_token %}` for these actions. The AJAX vote-up in `quotes_list.html` uses vanilla `fetch()` with the CSRF token read from a form on the page.

**Voting uses atomic F() expressions** to prevent race conditions from concurrent requests. Accept/reject use `update_fields` to avoid clobbering concurrent vote changes.

**Pagination** is handled by a shared `_paginate()` helper used by all list views (accepted, best, trash, manage). All lists paginate at 10 items per page.

There is a **logout view** (`logout_user`) that requires authentication and redirects to the index page. The navbar shows a logout link when the user is authenticated.

### Template filter

`{% load quote_extras %}` provides a `sub` filter for karma display: `{{ quote.votes_up|sub:quote.votes_down }}`. This replaced the third-party `django-mathfilters` package.

### Frontend stack

- **Bootstrap 5.3** via CDN (no jQuery dependency)
- **Bootstrap Icons** via CDN (replaced Glyphicons)
- **Vanilla JavaScript** for AJAX voting (replaced jQuery)
- No IE polyfills — modern browsers only

### Database configuration

`dj-database-url` parses `DATABASE_URL` env var. Falls back to SQLite at `db.sqlite3` in the project root. The Docker setup uses `/app/data/db.sqlite3` for the SQLite profile.

### Static files

WhiteNoise serves static files. `STATIC_ROOT = BASE_DIR / 'staticfiles'`. The `icons/` directory is in `STATICFILES_DIRS` so favicons are served at `/static/favicon.ico` etc.

`collectstatic` runs at Docker build time with a placeholder SECRET_KEY.

## Gotchas and things to watch out for

1. **Voting is not idempotent.** Each request atomically increments the counter via `F()` expressions. No session/IP tracking prevents repeated votes.

2. **`best_list` uses `annotate(karma=F('votes_up') - F('votes_down'))`** to compute karma in the database. The `karma` attribute is available on queryset results but is not a model field.

3. **The `SECRET_KEY` has a hardcoded fallback in settings.** This is fine for local dev but must be overridden via environment variable in production.

4. **`quote_ajax` returns JSON error responses** (400 for missing `quote_id`, 404 for non-existent quote) — the frontend JS does not currently display these errors to the user.

5. **Quote submission has a honeypot field** (`website`) for basic bot protection. The field is hidden from real users but bots that fill all fields will be rejected.

## Testing

Tests are in `quotes/tests.py` (96 tests, 15 classes):
- `QuoteModelTest` — model defaults, `__str__`, ordering, `SET_NULL` on user delete, status enum values
- `QuoteWorkflowTest` — full lifecycle (approve, reject, vote, delete, auth checks on all protected views, 404s on nonexistent quotes, list filtering by status, best ordering with downvotes, manage view content)
- `QuoteAddViewTest` — form submission, display, empty validation, correct templates, honeypot bot rejection
- `SafeRedirectTest` — malicious/safe/missing referer handling on public and protected views
- `QuoteDetailViewTest` — single quote view, 404, access to pending/rejected quotes
- `RequirePostTest` — GET returns 405 on all 6 POST-only endpoints
- `IndexViewTest` — home page rendering and template
- `LoginViewTest` — valid/invalid/empty credentials, already-authenticated redirect
- `LogoutViewTest` — redirect after logout, session invalidation, login required
- `QuoteAjaxTest` — JSON voting endpoint (success, 400, 404, karma calculation)
- `PaginationTest` — page size, multi-page navigation, invalid/out-of-range page handling, trash and manage pagination
- `ActiveNavTest` — verifies `active_nav` context variable on all public pages and manage view
- `TemplateFilterTest` — `sub` filter with normal, negative, zero, and invalid inputs
- `URLResolutionTest` — all 15 named URLs reverse correctly
- `FormTest` — field exposure, validation, status override prevention, honeypot field properties

Tests use Django's `TestCase` with the default test SQLite database. No fixtures — all data is created in `setUp` or individual tests. State-changing tests use `self.client.post()` matching the `@require_POST` enforcement on views.

Test runner is **pytest** with **pytest-django** and **pytest-cov**. Coverage threshold is 85% (currently at 99%). CI outputs JUnit XML for GitHub test reporting.

Run with: `SECRET_KEY=test DEBUG=True uv run --group dev pytest -v`

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):
1. **lint** — `uv run --group dev ruff check/format` (Python 3.12)
2. **test** — `uv sync --frozen --group dev` + `manage.py check` + `pytest --junitxml` with **dorny/test-reporter** for per-test pass/fail table on PRs
3. **docker** — builds the Docker image (runs after lint + test pass), uses GHA cache (`scope=docker-build`)

CI is also callable via `workflow_call` so the publish workflow can reuse it as a prerequisite. Both CI and publish share a GHA Docker layer cache (`scope=docker-build`) so publish gets near-instant cache hits after CI warms the cache.

Uses `astral-sh/setup-uv@v7` for fast, cached uv installs in CI.

### CodeQL security scanning

GitHub Actions (`.github/workflows/codeql.yml`):
- Runs GitHub's CodeQL static analysis on every push/PR to `master`
- Also runs weekly (Monday 06:00 UTC) to catch newly disclosed vulnerabilities
- Scans Python code for SQL injection, XSS, command injection, and other OWASP top-10 issues
- Results appear in the repository's **Security → Code scanning alerts** tab

### Dependabot

Configured in `.github/dependabot.yml`. Checks for updates **weekly on Mondays** across three ecosystems:

| Ecosystem | What it monitors | Labels |
|---|---|---|
| `uv` | `pyproject.toml` + `uv.lock` — Django, gunicorn, whitenoise, etc. | `dependencies`, `python` |
| `docker` | `Dockerfile` — `python:3.14-slim` base image, `ghcr.io/astral-sh/uv` | `dependencies`, `docker` |
| `github-actions` | Workflow action versions (`actions/checkout`, etc.) | `dependencies`, `ci` |

Dependabot PRs trigger the full CI pipeline (lint + test + docker build) automatically. Up to 5 open Python PRs at a time.

**Dependency cooldown** is enabled for Python packages to avoid churn from rapid-fire releases:
- Major updates: 14-day cooldown
- Minor updates: 7-day cooldown
- Patch updates: 3-day cooldown

Dependabot natively supports `uv` — it updates both `pyproject.toml` and `uv.lock` in the same PR.

Main branch is `master`.

### Publishing to GHCR

GitHub Actions (`.github/workflows/publish.yml`) — runs on pushes to `master` and version tags (`v*`), after CI passes:

1. **Build & push** — builds the Docker image and pushes to `ghcr.io/krzysztofahajdamowicz/bash.org-like`
2. **SBOM generation** — produces two CycloneDX JSON SBOMs via Syft (`anchore/sbom-action`):
   - `sbom-docker.cyclonedx.json` — full Docker image scan (OS packages, Python runtime, app dependencies)
   - `sbom-python.cyclonedx.json` — Python source dependencies only (from `pyproject.toml`/`uv.lock`)
3. **Attestations** — signs with Sigstore via `actions/attest@v4`:
   - Build provenance attestation (SLSA) attached to the container image
   - Docker image SBOM attestation attached to the container image
   - Python source SBOM attestation stored in GitHub
4. **Artifact upload** — both SBOMs are uploaded as downloadable workflow artifacts

Image tags produced by `docker/metadata-action`:

| Trigger | Tags |
|---|---|
| Push to `master` | `:master`, `:sha-<short>` |
| Tag `v1.2.3` | `:1.2.3`, `:1.2`, `:latest`, `:sha-<short>` |

The image name is lowercased from `github.repository` at runtime because OCI references require lowercase.

Permissions required: `packages: write`, `id-token: write` (Sigstore), `attestations: write`.

The workflow reuses CI via `workflow_call` (CI's `on:` includes `workflow_call:` for this purpose).

Verify attestations locally:
```bash
gh attestation verify oci://ghcr.io/krzysztofahajdamowicz/bash.org-like:latest --owner krzysztofahajdamowicz
```

## Deployment

- **Docker image**: published to `ghcr.io/krzysztofahajdamowicz/bash.org-like` (see [Publishing to GHCR](#publishing-to-ghcr))
- **Dockerfile**: multi-stage build, Python 3.14-slim, uv for installs, runs as non-root `app` user
- **docker-entrypoint.sh**: runs `migrate --noinput` then `exec "$@"`
- **docker-compose.yml**: three profiles — `sqlite`, `postgres`, `mariadb`
- **Gunicorn** serves the WSGI app on port 8000
- **Environment variables**: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`

## Code style

- **Formatter**: ruff (line-length 119, target py312)
- **No type hints** in the codebase
- **No docstrings** on views or models (except the `sub` template filter)
- Migration files are excluded from E501 linting
