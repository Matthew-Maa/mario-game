@echo off
cd /d "%~dp0"
title Mario Adventure

echo ================================
echo   Mario Adventure - Starting...
echo ================================
echo.

set "PYEXE="
where python >nul 2>&1 && set "PYEXE=python"
if not defined PYEXE (
    where py >nul 2>&1 && set "PYEXE=py"
)
if not defined PYEXE (
    echo [ERROR] Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)

%PYEXE% -c "import pygame" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies: pygame-ce numpy
    %PYEXE% -m pip install pygame-ce numpy
)

echo Starting game...
%PYEXE% main.py
pause
