@echo off
REM Setup and run script for queuectl

echo ========================================
echo queuectl Setup and Run
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not found in PATH.
    echo Please install Python 3.7+ and add it to your PATH.
    echo.
    echo You can download Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo You can now run:
echo   python main.py --help
echo   python main.py enqueue "{\"command\":\"echo hello\"}"
echo   python main.py worker start --count 1
echo.
pause

