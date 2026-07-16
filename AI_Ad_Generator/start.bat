@echo off
title AI Ad Generator

if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py
pause
