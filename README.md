\# MatchFlow



Веб-приложение для организации любительских футбольных команд, матчей и мини-турниров.



\## Запуск backend



```bash

python -m venv .venv

.venv\\Scripts\\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

python manage.py seed\_demo

python manage.py runserver 8000

