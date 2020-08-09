@echo off
call clean.bat
pip install -r requirements.txt
IF EXIST "build" (
    RMDIR /S /Q build
)
IF EXIST "dist" (
    RMDIR /S /Q dist
)
IF EXIST "__pycache__" (
    RMDIR /S /Q __pycache__
)
IF EXIST "main.spec" (
    ERASE main.spec
)
pyinstaller --onefile --uac-admin --icon=app.ico main.py