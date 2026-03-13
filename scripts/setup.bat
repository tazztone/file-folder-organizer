@echo off
echo Setting up Pro File Organizer with uv...

REM Check for uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo uv is not installed or not in PATH. Please install it from https://github.com/astral-sh/uv
    pause
    exit /b
)

REM Create venv if not exists
if not exist "venv" (
    echo Creating virtual environment using uv...
    uv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install requirements (if any)
if exist "requirements.txt" (
    uv pip install -r requirements.txt
)

echo.
echo Setup complete. To run the app:
echo venv\Scripts\activate
echo python app.py
echo.
pause
