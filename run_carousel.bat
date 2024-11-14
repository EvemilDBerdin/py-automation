@echo off
echo Starting Lamudi Property Automation Setup...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install playwright
python -m playwright install

REM Check if the Python script exists
if not exist browser_carousel.py (
    echo Error: browser_carousel.py not found in current directory
    exit /b 1
)

REM Run the Python script
echo Starting automation...
python browser_carousel.py

echo Script execution completed
pause