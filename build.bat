@echo off
pip install -r requirements.txt
python -m PyInstaller --clean --onefile --uac-admin --noconsole --icon=app.ico -n=chronos-installer main.py