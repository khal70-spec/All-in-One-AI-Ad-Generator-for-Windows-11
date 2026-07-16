@echo off
title AI Ad Generator - Installer
color 0A
echo ============================================
echo    AI AD GENERATOR - WINDOWS 11 INSTALLER
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from python.org
    echo Make sure to check "Add Python to PATH"
    pause
    start https://www.python.org/downloads/
    exit
)

echo [OK] Python found
echo.

:: Create virtual environment
echo [1/5] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

:: Upgrade pip
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip

:: Install PyTorch with CUDA
echo [3/5] Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

:: Install requirements
echo [4/5] Installing dependencies...
pip install -r requirements.txt

:: Create directories
echo [5/5] Creating directories...
mkdir models 2>nul
mkdir outputs 2>nul
mkdir temp 2>nul
mkdir assets 2>nul

echo.
echo ============================================
echo    INSTALLATION COMPLETE!
echo ============================================
echo.
echo Run 'start.bat' to launch the application
echo.
pause
