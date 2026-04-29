@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   RONIN GLOBAL INSTALLER
echo ========================================

:: 1. Check for Virtual Environment
if not "%VIRTUAL_ENV%"=="" (
    echo.
    echo [!] WARNING: You are running inside a virtual environment: %VIRTUAL_ENV%
    echo To make 'ronin' accessible globally everywhere across your computer,
    echo please type 'deactivate' and re-run this installer.
    echo.
    pause
    exit /b
)

echo.
echo [1/4] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/4] Installing dependencies ^& standalone package...
pip install -e .

echo.
echo [3/4] Ensuring command is on your system PATH...
:: Find Python's Scripts directory
FOR /F "tokens=*" %%i IN ('python -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts'))"') DO SET PYTHON_SCRIPTS=%%i

echo Python Scripts directory: %PYTHON_SCRIPTS%

:: Check if Scripts is already in User PATH
echo %PATH% | findstr /I /C:"%PYTHON_SCRIPTS%" >nul
if %errorlevel% neq 0 (
    echo Adding directory to User PATH...
    setx PATH "%PATH%;%PYTHON_SCRIPTS%"
    echo.
    echo [*] Added to PATH persistently.
    echo     NOTE: You MUST restart your terminal or VS Code window for this to take effect.
) else (
    echo [*] Directory is already present on system PATH.
)

echo.
echo [4/4] Configuring Global credentials...
set /p API_KEY="Paste your GEMINI_API_KEY (leave blank to skip): "

set CONFIG_DIR=%USERPROFILE%\.ronin
set CONFIG_FILE=%CONFIG_DIR%\.env

if not "%API_KEY%"=="" (
    if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
    echo MODEL=gemini> "%CONFIG_FILE%"
    echo MODEL_NAME=gemini-3-flash>> "%CONFIG_FILE%"
    echo GEMINI_API_KEY=%API_KEY%>> "%CONFIG_FILE%"
    echo Global credentials saved successfully to %CONFIG_FILE%
) else (
    echo Skipping key configuration.
)

echo.
echo ========================================
echo   SUCCESS! Setup Complete.
echo   Close this window, open a NEW terminal, and run:
echo   ronin "your prompt"
echo ========================================
pause

