@echo off
echo Setting up Pro File Organizer...

REM Check for python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Create venv if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements (if any)
if exist "requirements.txt" (
    pip install -r requirements.txt
)

echo.
echo Setup complete. To run the app:
echo venv\Scripts\activate
echo python app.py
echo.
pause
