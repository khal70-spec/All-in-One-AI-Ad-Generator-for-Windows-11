@echo off
title Building AI Ad Generator
call venv\Scripts\activate.bat

echo Installing PyInstaller...
pip install pyinstaller

echo Building executable...
pyinstaller --onedir ^
    --name "AI_Ad_Generator" ^
    --windowed ^
    --add-data "assets;assets" ^
    --add-data "config.py;." ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import torch ^
    --hidden-import diffusers ^
    --collect-all customtkinter ^
    main.py

echo.
echo Build complete! Check the 'dist' folder.
pause
