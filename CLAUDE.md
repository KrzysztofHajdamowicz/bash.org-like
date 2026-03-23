# CLAUDE.md — bash.org-like

## Project overview

A **bash.org-like quote database** built with Django. Users submit IRC/chat-style quotes, moderators approve or reject them, and anyone can upvote/downvote approved quotes. Think bash.org but self-hosted.

- **Django 6.0.3** on **Python 3.12+**
- Single Django app: `quotes`
- Function-based views (no CBVs)
- SQLite by default, PostgreSQL and MariaDB via `DATABASE_URL`
- Bootstrap 3.3.7 frontend with jQuery for AJAX voting

## Quick commands

```bash
# Run dev server (set env vars or use defaults)
SECRET_KEY=dev DEBUG=True python manage.py runserver

# Run tests (17 tests)
SECRET_KEY=test DEBUG=True python manage.py test

# Lint
ruff check . && ruff format --check .

# Generate migrations after model changes
SECRET_KEY=test python manage.py makemigrations

# Docker (pick a profile: sqlite, postgres, mariadb)
docker compose --profile sqlite up --build
```

## Project structure

```
BashOrgLike/             # Django project package
  settings.py            # All config — env-driven (SECRET_KEY, DEBUG, DATABASE_URL, ALLOWED_HOSTS)
  urls.py                # Root URL conf — admin + includes quotes.urls
  wsgi.py                # WSGI entry point for gunicorn

quotes/                  # The single Django app
  models.py              # Quote model (the only model)
  views.py               # 14 function-based views
  urls.py                # 14 URL patterns, all using path()
  forms.py               # AddQuoteForm (ModelForm, content field only)
  tests.py               # 17 tests across 4 test classes
  admin.py               # Quote registered in Django admin
  apps.py                # QuotesConfig
  templatetags/
    quote_extras.py      # Custom `sub` filter (karma = votes_up - votes_down)
  templates/quotes/
    base.html            # Bootstrap 3 layout, navbar, static assets
    welcome.html         # Home page
    quotes_list.html     # Paginated quote list (accepted + best + trash views share this)
    quotes_view.html     # Single quote detail
    quote_add.html       # Submit new quote form
    quote_added.html     # Success page after submission
    quotes_manage.html   # Moderation panel (login required)
    login_form.html      # Login page
    paginator.html       # Reusable pagination partial

icons/                   # Favicons and PWA manifest (served as static files)
```

## Architecture and design

### The Quote model

The only model. Status is an integer field, not an enum:

| Value | Meaning    |
|-------|------------|
| 1     | Pending    |
| 2     | Rejected   |
| 3     | Approved   |

These magic numbers are used directly in view queries (`status=3`, `status=1`, etc.) rather than through named constants. `STATUS_CHOICES` is defined at module level in `models.py` but the views hardcode the integers.

Key fields:
- `content` — the quote text (TextField)
- `votes_up` / `votes_down` — separate counters (PositiveIntegerField), not a net score
- `acceptant` — ForeignKey to User (SET_NULL), the moderator who approved/rejected
- `created_date` — auto_now_add, used for default ordering
- `status` — integer with choices, defaults to 1 (pending)

`DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'` — the pk is a BigAutoField.

### Views pattern

All views are plain functions. The codebase does **not** use class-based views.

Every `render()` call passes `site_name` and `context` (a string identifying the active nav tab — not to be confused with template context). This `context` string drives the active state in the navbar via `{% if context == 'accepted_list' %}`.

Auth-protected views use `@login_required(login_url='/login/')`. There is no LoginRequiredMiddleware — most pages are public.

State-changing operations (accept, reject, delete, vote) use **GET requests** and redirect back via `HTTP_REFERER`. This is a known design choice, not a bug.

### Template filter

`{% load quote_extras %}` provides a `sub` filter for karma display: `{{ quote.votes_up|sub:quote.votes_down }}`. This replaced the third-party `django-mathfilters` package.

### Database configuration

`dj-database-url` parses `DATABASE_URL` env var. Falls back to SQLite at `db.sqlite3` in the project root. The Docker setup uses `/app/data/db.sqlite3` for the SQLite profile.

### Static files

WhiteNoise serves static files. `STATIC_ROOT = BASE_DIR / 'staticfiles'`. The `icons/` directory is in `STATICFILES_DIRS` so favicons are served at `/static/favicon.ico` etc.

`collectstatic` runs at Docker build time with a placeholder SECRET_KEY.

## Gotchas and things to watch out for

1. **Status integers are hardcoded everywhere.** The views use `status=3`, `status=2`, `status=1` directly. If you add or change statuses, grep the entire codebase — views, templates, and tests all assume these values.

2. **`quote_add` view has a subtle bug.** On POST with invalid form data, it returns `None` (falls through without returning a response). Only valid POST and GET are handled with explicit returns.

3. **State-changing actions accept GET requests.** Vote, accept, reject, and delete all work via GET. This means crawlers or prefetch could trigger actions. The moderation actions are behind `@login_required` but voting endpoints are fully public and unprotected.

4. **`login_user` view calls `logout()` on every non-authenticated request** before checking credentials. This is intentional but unusual.

5. **`login_user` has a `print(settings.SITE_NAME)` debug statement** that runs on every request to the login page.

6. **AJAX vote endpoint (`quote_ajax`) has no error handling.** If `quote_id` is missing from GET params or doesn't match a quote, it raises an unhandled exception (KeyError or Quote.DoesNotExist).

7. **Voting is not idempotent.** Each request increments the counter. No session/IP tracking prevents repeated votes.

8. **The `context` template variable name shadows Django terminology.** It's just a string for navbar highlighting, not a template context dict.

9. **Mixed language in UI.** The moderation panel buttons are in Polish ("Zaakceptuj", "Odrzuc", "Usun") while the rest of the site is English.

10. **`quote_view` always sets `context='accepted_list'`** regardless of how the user navigated there, so the "Accepted" nav tab is always highlighted on detail pages.

11. **`best_list` uses `annotate(karma=F('votes_up') - F('votes_down'))`** to compute karma in the database. The `karma` attribute is available on queryset results but is not a model field.

12. **No CSRF protection on vote endpoints.** Voting views use GET requests so CSRF middleware doesn't apply, but this also means any page can trigger votes via image tags or links.

13. **The `SECRET_KEY` has a hardcoded fallback in settings.** This is fine for local dev but must be overridden via environment variable in production.

## Testing

Tests are in `quotes/tests.py` (17 tests, 4 classes):
- `QuoteModelTest` — model defaults and `__str__`
- `QuoteWorkflowTest` — full lifecycle (approve, reject, vote, delete, auth checks, list filtering, best ordering)
- `QuoteAddViewTest` — form submission and display
- `QuoteDetailViewTest` — single quote view and 404

Tests use Django's `TestCase` with the default test SQLite database. No fixtures — all data is created in `setUp` or individual tests.

Run with: `SECRET_KEY=test DEBUG=True python manage.py test`

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):
1. **lint** — ruff check + format check (Python 3.12)
2. **test** — pip install, `manage.py check`, `manage.py test`
3. **docker** — builds the Docker image (runs after lint + test pass)

Main branch is `master`.

## Deployment

- **Dockerfile**: multi-stage build, Python 3.12-slim, runs as non-root `app` user
- **docker-entrypoint.sh**: runs `migrate --noinput` then `exec "$@"`
- **docker-compose.yml**: three profiles — `sqlite`, `postgres`, `mariadb`
- **Gunicorn** serves the WSGI app on port 8000
- **Environment variables**: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`

## Code style

- **Formatter**: ruff (line-length 119, target py312)
- **No type hints** in the codebase
- **No docstrings** on views or models (except the `sub` template filter)
- Migration files are excluded from E501 linting
