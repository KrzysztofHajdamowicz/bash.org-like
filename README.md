# bash.org-like
Simple script with bash.org functionality - perfect for making a quote database.

Script is written in Django as a my first project in this programming language.  
It's meant to be a bash.org "replacement" as I've been looking for simmilar tool about a year ago and I've found only legacy PHP 4.x stuff that barely runs at PHP 5.5/5.6 and required some code refactoring to actually run

### Installing
```Bash
git clone https://github.com/KrzysztofHajdamowicz/bash.org-like.git
cd bash.org-like
virtualenv venv
source venv/bin/activate
pip install $(cat requirements.txt )
python manage.py migrate
python manage.py runserver
```

