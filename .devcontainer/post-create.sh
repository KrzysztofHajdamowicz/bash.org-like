#!/bin/bash
set -e

pip install -r requirements.txt
python manage.py migrate

if [ -f db.sqlite3 ]; then
    python manage.py runserver 0.0.0.0:8000 &
fi
