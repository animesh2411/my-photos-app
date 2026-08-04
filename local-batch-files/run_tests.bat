@echo off
title PhotoBridge Test Runner
cd /d "%~dp0.."

if not exist ".venv" (
    echo [ERROR] Python Virtual Environment (.venv) not found.
    echo Please run run_control_center.bat first to set up the environment.
    pause
    exit /b 1
)

echo [TESTS] Activating Virtual Environment...
call .venv\Scripts\activate.bat

echo [TESTS] Running backend unit tests with coverage...
set PYTHONPATH=backend
pytest --cov=backend/app --cov-report=term-missing tests/

pause
