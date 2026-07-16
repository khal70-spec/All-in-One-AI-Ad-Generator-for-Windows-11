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

:: Create virtual environment (skip if it already exists)
if exist venv\Scripts\activate.bat (
    echo [1/5] Virtual environment already exists - reusing it
) else (
    echo [1/5] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo Try: python -m pip install --user virtualenv
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat

:: Upgrade pip
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip

:: Install PyTorch - CUDA build when an NVIDIA GPU is present, CPU otherwise
echo [3/5] Installing PyTorch...
nvidia-smi >nul 2>&1
if %errorlevel%==0 (
    echo     NVIDIA GPU detected - installing CUDA 12.1 build
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo     No NVIDIA GPU detected - installing CPU build
    echo     ^(generation will work but be much slower^)
    pip install torch torchvision torchaudio
)

:: Install requirements
echo [4/5] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed. See messages above.
    pause
    exit /b 1
)

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
