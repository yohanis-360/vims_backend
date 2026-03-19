@echo off
REM Run Django so the mobile verify app can connect from your phone.
REM Use this machine's LAN IP in the app (e.g. http://192.168.100.186:8000)
python manage.py runserver 0.0.0.0:8000
