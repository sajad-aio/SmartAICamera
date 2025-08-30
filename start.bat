@echo off
title Face Recognition System
color 0A

echo.
echo ========================================
echo    Face Recognition System Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment not found
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo 🚀 Starting Face Recognition System...
echo.

REM Run the application
python run.py

echo.
echo 👋 Application closed
pause