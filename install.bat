@echo off
echo ========================================
echo   RONIN GLOBAL INSTALLER
echo ========================================

echo.
echo [1/3] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/3] Installing dependencies...
pip install -r requirements.txt

echo.
echo [3/3] Registering global 'ronin' command...
pip install -e .

echo.
echo ========================================
echo   SUCCESS! 
echo   You can now run 'ronin "task"' anywhere.
echo ========================================
pause
