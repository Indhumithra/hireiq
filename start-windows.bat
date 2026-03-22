@echo off
setlocal

echo ==============================================
echo   HireIQ AI Resume Screener - Startup Script
echo ==============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :python_found
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :python_found
)

:: Python not found, try to install it automatically
echo [INFO] Python not found on this system.
echo [INFO] Downloading Python 3.11 automatically... this might take a moment.
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe' -OutFile 'python_installer.exe'"

echo [INFO] Installing Python 3.11 silently... please wait.
start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1

:: Clean up installer
del python_installer.exe

:: Try to use the newly installed python path directly since PATH updates require terminal restart
set "PYTHON_CMD=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PYTHON_CMD%" (
    echo [ERROR] Automatic Python installation failed or path was unexpected. 
    echo Please install Python 3.8+ manually from python.org and check the box "Add Python to PATH".
    pause
    exit /b 1
)
echo [INFO] Python installed successfully!

:python_found
echo [INFO] Using Python command: "%PYTHON_CMD%"

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating Python virtual environment...
    "%PYTHON_CMD%" -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment. Make sure python is working.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install requirements
echo [INFO] Installing required dependencies (this may take a few minutes for AI libraries)...
"%PYTHON_CMD%" -m pip install --upgrade pip
pip install -r requirements.txt

:: Run the application
echo.
echo [INFO] Starting the HireIQ application...
echo [INFO] The local server will be available at http://localhost:5000
echo [INFO] Your browser will open automatically in a few seconds...
echo ==============================================

:: Open browser in the background with a 3-second delay to allow the server to boot
start /b powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:5000'"

python run.py

pause
