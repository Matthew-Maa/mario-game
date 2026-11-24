@echo off
cd /d "%~dp0"
title Mario Adventure - Build Tool

set "PYEXE="
where python >nul 2>&1 && set "PYEXE=python"
if not defined PYEXE (
    where py >nul 2>&1 && set "PYEXE=py"
)
if not defined PYEXE (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

%PYEXE% -m pip install pygame-ce numpy pyinstaller

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "MarioAdventure.spec" del "MarioAdventure.spec"

%PYEXE% -m PyInstaller --noconfirm --onedir --windowed ^
    --name "MarioAdventure" ^
    --add-data "assets;assets" ^
    --add-data "constants.py;." ^
    --add-data "player.py;." ^
    --add-data "enemy.py;." ^
    --add-data "level_data.py;." ^
    --add-data "menu.py;." ^
    --add-data "game.py;." ^
    --add-data "settings_manager.py;." ^
    --add-data "save_manager.py;." ^
    --add-data "achievement_manager.py;." ^
    --add-data "transitions.py;." ^
    --add-data "asset_generator.py;." ^
    --hidden-import "pygame" ^
    --hidden-import "pygame.locals" ^
    main.py

echo Build done: dist\MarioAdventure\
pause
