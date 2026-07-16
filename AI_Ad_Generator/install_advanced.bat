@echo off
title AI Ad Generator - Advanced Models
color 0B
echo ============================================
echo    AI AD GENERATOR - ADVANCED MODELS
echo ============================================
echo.
echo This upgrades diffusers / transformers / accelerate so you can use
echo the heavier models: Mochi 1, HunyuanVideo, LTX-Video.
echo.
echo (Install the base requirements first with install.bat)
echo.

if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Upgrading dependencies for advanced models...
pip install -r requirements_advanced.txt

echo.
echo Done! You can now download and use the advanced models.
echo.
pause
