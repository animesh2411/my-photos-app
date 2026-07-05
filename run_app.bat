@echo off
:: Title of the console window
title PhotoBridge Launcher

echo ======================================================================
echo                     PhotoBridge PWA Server Launcher
echo ======================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo.
    echo Please install Python 3.11 or later from https://www.python.org/
    echo Make sure to check the option "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Create a virtual environment if it doesn't exist
if not exist ".venv" (
    echo [SETUP] Creating isolated Python Virtual Environment venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
echo [SETUP] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Install/update dependencies
echo [SETUP] Checking and installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [SERVER] Starting PhotoBridge server...
echo.

:: Run the server
python run.py

:: If python finishes (e.g. user stopped it), clean up and exit
echo.
echo [SERVER] Server stopped.
echo.
pause
