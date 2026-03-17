@echo off
title ICA PMS - Build EXE
color 1F
echo.
echo  ============================================================
echo    ICA PMS  ^|  Building EXE
echo  ============================================================
echo.

echo  [1/4] Installing Python packages...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 ( echo  FAILED: pip install & pause & exit /b 1 )
python -m pip install pyinstaller
if %errorlevel% neq 0 ( echo  FAILED: pyinstaller & pause & exit /b 1 )

echo  [2/4] Creating icon...
python _make_icon.py

echo.
echo  [3/4] Building ICA_PMS.exe  (5-15 mins, please wait)...
echo         Lots of text below is normal - do not close this window.
echo.
set ICA_EXE_NAME=ICA_PMS
python -m PyInstaller app.spec --clean --noconfirm --distpath dist
if %errorlevel% neq 0 ( echo  FAILED: Build failed & pause & exit /b 1 )

echo  [4/4] Cleaning temp files...
rmdir /s /q build 2>nul

echo.
echo  ============================================================
echo    DONE!
echo    Your EXE is ready at:  dist\ICA_PMS.exe
echo    Send this file to your client.
echo  ============================================================
echo.
pause
