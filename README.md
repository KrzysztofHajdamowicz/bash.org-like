# bash.org-like

Simple script with bash.org functionality - perfect for making a quote database.

Script is written in Django as a my first project in this programming language.
It's meant to be a bash.org "replacement" as I've been looking for similar tool about a year ago and I've found only legacy PHP 4.x stuff that barely runs at PHP 5.5/5.6 and required some code refactoring to actually run.

## Requirements

- Python 3.11+
- Django 4.2.x

## Getting started

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/KrzysztofHajdamowicz/bash.org-like.git
cd bash.org-like
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run database migrations

```bash
python manage.py migrate
```

### 4. Create a superuser (optional, for the admin panel and quote moderation)

```bash
python manage.py createsuperuser
```

### 5. Start the development server

```bash
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

## Production deployment

### Environment variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | hard-coded fallback (change in production!) |
| `DEBUG` | Enable debug mode (`true`/`1`/`yes`) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `*` |

### Running with Gunicorn

```bash
export SECRET_KEY="your-production-secret-key"
export DEBUG=false
export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"

python manage.py collectstatic --noinput
python manage.py migrate

gunicorn BashOrgLike.wsgi:application --bind 0.0.0.0:8000
```
