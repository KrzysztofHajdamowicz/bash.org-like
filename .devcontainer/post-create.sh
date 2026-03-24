#!/bin/bash
set -e

# Install uv if not available
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

uv sync
uv run python manage.py migrate

if [ -f db.sqlite3 ]; then
    uv run python manage.py runserver 0.0.0.0:8000 &
fi
