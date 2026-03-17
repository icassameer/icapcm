@echo off
title ICA PMS - Build DEMO Version
color 4F
echo.
echo  ============================================================
echo    ICA PMS  ^|  DEMO EXE  ^|  5-Day Trial
echo  ============================================================
echo.

echo  [1/5] Installing Python packages (please wait)...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 ( echo  FAILED: pip install & pause & exit /b 1 )
python -m pip install pyinstaller
if %errorlevel% neq 0 ( echo  FAILED: pyinstaller install & pause & exit /b 1 )

echo.
echo  [2/5] Switching to DEMO edition...
python _set_edition.py DEMO
if %errorlevel% neq 0 ( echo  FAILED: set edition & pause & exit /b 1 )

echo  [3/5] Creating icon...
python _make_icon.py

echo.
echo  [4/5] Building EXE (this takes 5-15 mins, please wait)...
echo         You will see a lot of text below - that is normal.
echo.
set ICA_EXE_NAME=ICA_PMS_Demo
python -m PyInstaller app.spec --clean --noconfirm --distpath dist
if %errorlevel% neq 0 (
    echo  FAILED: PyInstaller build
    python _set_edition.py FULL
    pause & exit /b 1
)

echo  [5/5] Restoring FULL edition + cleaning up...
python _set_edition.py FULL
rmdir /s /q build 2>nul

echo.
echo  ============================================================
echo    DONE!   dist\ICA_PMS_Demo.exe  is ready to send to client
echo  ============================================================
echo.
pause
