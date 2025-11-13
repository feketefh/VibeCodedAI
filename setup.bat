@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM JARVIS AI Assistant - Automated Setup Script
REM ============================================================

color 0A
title JARVIS Setup - Automated Installation

echo.
echo ============================================================
echo    JARVIS AI ASSISTANT - AUTOMATED SETUP
echo ============================================================
echo.
echo This script will:
echo   [1] Check system requirements
echo   [2] Create Python virtual environment
echo   [3] Install all dependencies
echo   [4] Verify installation
echo.
pause

REM ============================================================
REM CHECK ADMINISTRATOR PRIVILEGES
REM ============================================================
echo.
echo [STEP 1/6] Checking administrator privileges...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
) else (
    echo [WARNING] Not running as administrator
    echo Some features might not install correctly
    echo Right-click setup.bat and select "Run as administrator"
    echo.
    pause
)

REM ============================================================
REM CHECK PYTHON INSTALLATION
REM ============================================================
echo.
echo [STEP 2/6] Checking Python installation...

python --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [OK] Python !PYTHON_VERSION! found
    
    REM Check Python version (needs 3.8+)
    for /f "tokens=1 delims=." %%a in ("!PYTHON_VERSION!") do set MAJOR=%%a
    for /f "tokens=2 delims=." %%a in ("!PYTHON_VERSION!") do set MINOR=%%a
    
    if !MAJOR! LSS 3 (
        echo [ERROR] Python 3.8+ required, found !PYTHON_VERSION!
        goto :error_python
    )
    if !MAJOR! EQU 3 if !MINOR! LSS 8 (
        echo [ERROR] Python 3.8+ required, found !PYTHON_VERSION!
        goto :error_python
    )
) else (
    echo [ERROR] Python not found!
    goto :error_python
)

REM ============================================================
REM CHECK VISUAL STUDIO C++ BUILD TOOLS
REM ============================================================
echo.
echo [STEP 3/6] Checking Visual Studio C++ Build Tools...

set VS_FOUND=0

REM Check for VS 2022
if exist "C:\Program Files\Microsoft Visual Studio\2022" (
    echo [OK] Visual Studio 2022 found
    set VS_FOUND=1
)

REM Check for VS 2019
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019" (
    echo [OK] Visual Studio 2019 found
    set VS_FOUND=1
)

REM Check for VS Build Tools
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools" (
    echo [OK] Visual Studio Build Tools 2022 found
    set VS_FOUND=1
)

if !VS_FOUND! == 0 (
    echo [WARNING] Visual Studio C++ Build Tools not found
    echo.
    echo Some Python packages (like cryptography, bcrypt) need C++ compiler
    echo.
    echo You have 2 options:
    echo   1. Install Visual Studio Build Tools (Recommended)
    echo   2. Continue anyway (some features might not work)
    echo.
    echo To install Build Tools:
    echo   Download from: https://visualstudio.microsoft.com/downloads/
    echo   Install "Desktop development with C++" workload
    echo.
    choice /C 12 /M "Choose option"
    if errorlevel 2 (
        echo Continuing without Build Tools...
    ) else (
        echo Please install Build Tools and run this script again
        start https://visualstudio.microsoft.com/downloads/
        pause
        exit /b 1
    )
) else (
    echo [OK] C++ Build Tools detected
)

REM ============================================================
REM CHECK/INSTALL PIP
REM ============================================================
echo.
echo [STEP 4/6] Checking pip installation...

python -m pip --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] pip is installed
    echo Upgrading pip...
    python -m pip install --upgrade pip --quiet
) else (
    echo [WARNING] pip not found, installing...
    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
)

REM ============================================================
REM CREATE VIRTUAL ENVIRONMENT
REM ============================================================
echo.
echo [STEP 5/6] Creating virtual environment...

if exist ".venv" (
    echo [WARNING] Virtual environment already exists
    choice /C YN /M "Do you want to recreate it? (This will delete existing .venv)"
    if errorlevel 2 (
        echo Keeping existing virtual environment...
    ) else (
        echo Removing old virtual environment...
        rmdir /s /q .venv
        echo Creating new virtual environment...
        python -m venv .venv
    )
) else (
    echo Creating virtual environment...
    python -m venv .venv
)

if not exist ".venv" (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)

echo [OK] Virtual environment created: .venv

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo [OK] Virtual environment activated

REM ============================================================
REM INSTALL DEPENDENCIES
REM ============================================================
echo.
echo [STEP 6/6] Installing dependencies...
echo This may take 5-10 minutes depending on your internet speed...
echo.

REM Upgrade pip in venv
python -m pip install --upgrade pip setuptools wheel --quiet

echo.
echo [1/4] Installing CORE dependencies (required)...
python -m pip install cryptography bcrypt --quiet
if %errorLevel% == 0 (
    echo [OK] Core dependencies installed
) else (
    echo [WARNING] Some core dependencies failed to install
    echo This might be due to missing C++ Build Tools
)

echo.
echo [2/4] Installing AI dependencies (recommended)...
echo.
echo Choose AI backend:
echo   [1] Ollama (RECOMMENDED - Best quality, streaming, web search)
echo   [2] GPT4All + Transformers (Offline fallback)
echo   [3] Skip AI features
echo.
choice /C 123 /M "Select option"

if errorlevel 3 (
    echo Skipping AI dependencies...
    set INSTALL_AI=0
) else if errorlevel 2 (
    echo Installing GPT4All and Transformers...
    python -m pip install transformers torch gpt4all --quiet
    
    if %errorLevel% == 0 (
        echo [OK] AI dependencies installed
        set INSTALL_AI=1
    ) else (
        echo [WARNING] AI dependencies installation had issues
        set INSTALL_AI=0
    )
) else (
    echo Installing Ollama Python package...
    python -m pip install ollama duckduckgo-search pyyaml --quiet
    
    if %errorLevel% == 0 (
        echo [OK] Ollama Python package installed
        set INSTALL_AI=1
        
        echo.
        echo IMPORTANT: You need to install Ollama application separately!
        echo.
        echo Steps:
        echo   1. Download from: https://ollama.ai/download
        echo   2. Install Ollama
        echo   3. Run: ollama pull llama3.2
        echo.
        choice /C YN /M "Open Ollama download page now?"
        if errorlevel 2 (
            echo You can download later from: https://ollama.ai/download
        ) else (
            start https://ollama.ai/download
            echo Please install Ollama and run: ollama pull llama3.2
        )
    ) else (
        echo [WARNING] Ollama package installation had issues
        set INSTALL_AI=0
    )
)

echo.
echo [3/4] Installing VISION dependencies (optional)...
choice /C YN /M "Install computer vision (OpenCV, YOLO)?"
if errorlevel 2 (
    echo Skipping vision dependencies...
    set INSTALL_VISION=0
) else (
    echo Installing OpenCV and Ultralytics...
    python -m pip install opencv-python ultralytics --quiet
    
    if %errorLevel% == 0 (
        echo [OK] Vision dependencies installed
        set INSTALL_VISION=1
    ) else (
        echo [WARNING] Vision dependencies installation had issues
        set INSTALL_VISION=0
    )
)

echo.
echo [4/4] Installing 3D RENDERING dependencies (optional)...
choice /C YN /M "Install 3D rendering (PyVista, Matplotlib)?"
if errorlevel 2 (
    echo Skipping 3D dependencies...
    set INSTALL_3D=0
) else (
    echo Installing PyVista and Matplotlib...
    python -m pip install pyvista matplotlib --quiet
    
    if %errorLevel% == 0 (
        echo [OK] 3D rendering dependencies installed
        set INSTALL_3D=1
    ) else (
        echo [WARNING] 3D rendering dependencies installation had issues
        set INSTALL_3D=0
    )
)

echo.
echo [BONUS] Installing Text-to-Speech (pyttsx3)...
python -m pip install pyttsx3 --quiet
if %errorLevel% == 0 (
    echo [OK] Text-to-Speech installed
)

REM ============================================================
REM VERIFY INSTALLATION
REM ============================================================
echo.
echo.
echo ============================================================
echo VERIFYING INSTALLATION...
echo ============================================================
echo.

python -c "import cryptography; print('[OK] Cryptography')" 2>nul || echo [FAILED] Cryptography
python -c "import bcrypt; print('[OK] Bcrypt')" 2>nul || echo [FAILED] Bcrypt
python -c "import pyttsx3; print('[OK] Text-to-Speech')" 2>nul || echo [WARNING] Text-to-Speech

if !INSTALL_AI! == 1 (
    python -c "import transformers; print('[OK] Transformers')" 2>nul || echo [FAILED] Transformers
    python -c "import gpt4all; print('[OK] GPT4All')" 2>nul || echo [FAILED] GPT4All
)

if !INSTALL_VISION! == 1 (
    python -c "import cv2; print('[OK] OpenCV')" 2>nul || echo [FAILED] OpenCV
    python -c "import ultralytics; print('[OK] YOLO')" 2>nul || echo [FAILED] YOLO
)

if !INSTALL_3D! == 1 (
    python -c "import pyvista; print('[OK] PyVista')" 2>nul || echo [FAILED] PyVista
    python -c "import matplotlib; print('[OK] Matplotlib')" 2>nul || echo [FAILED] Matplotlib
)

REM ============================================================
REM CREATE LAUNCH SCRIPTS
REM ============================================================
echo.
echo Creating launch scripts...

REM Create run.bat
echo @echo off > run.bat
echo call .venv\Scripts\activate.bat >> run.bat
echo python jarvis_main.py >> run.bat
echo pause >> run.bat

REM Create run_test.bat
echo @echo off > run_test.bat
echo call .venv\Scripts\activate.bat >> run_test.bat
echo echo Testing JARVIS components... >> run_test.bat
echo echo. >> run_test.bat
echo python jarvis_logic_ai_enhanced.py >> run_test.bat
echo pause >> run_test.bat

echo [OK] Launch scripts created: run.bat, run_test.bat

REM ============================================================
REM INSTALLATION COMPLETE
REM ============================================================
echo.
echo.
echo ============================================================
echo    INSTALLATION COMPLETE!
echo ============================================================
echo.
echo Virtual Environment: .venv
echo Python Version: !PYTHON_VERSION!
echo.
echo INSTALLED FEATURES:
echo   [X] Core Security (Cryptography, Bcrypt)
if !INSTALL_AI! == 1 echo   [X] AI Intelligence (Transformers, GPT4All)
if !INSTALL_VISION! == 1 echo   [X] Computer Vision (OpenCV, YOLO)
if !INSTALL_3D! == 1 echo   [X] 3D Rendering (PyVista, Matplotlib)
echo   [X] Text-to-Speech (pyttsx3)
echo.
echo TO RUN JARVIS:
echo   Option 1: Double-click run.bat
echo   Option 2: Run manually:
echo             .venv\Scripts\activate.bat
echo             python jarvis_main.py
echo.
echo TO TEST COMPONENTS:
echo   Double-click run_test.bat
echo.
echo TROUBLESHOOTING:
echo   - If imports fail, install Visual Studio Build Tools
echo   - AI models download automatically on first use
echo   - Check jarvis_full_data folder for logs
echo.
echo ============================================================
echo.

choice /C YN /M "Do you want to run JARVIS now?"
if errorlevel 2 (
    echo.
    echo Thank you! Run "run.bat" when ready.
    pause
    exit /b 0
) else (
    echo.
    echo Starting JARVIS...
    echo.
    python jarvis_main.py
)

exit /b 0

REM ============================================================
REM ERROR HANDLERS
REM ============================================================
:error_python
echo.
echo ============================================================
echo PYTHON NOT FOUND OR VERSION TOO OLD
echo ============================================================
echo.
echo Please install Python 3.8 or newer:
echo   Download from: https://www.python.org/downloads/
echo.
echo IMPORTANT: During installation, check:
echo   [X] Add Python to PATH
echo   [X] Install pip
echo.
start https://www.python.org/downloads/
pause
exit /b 1