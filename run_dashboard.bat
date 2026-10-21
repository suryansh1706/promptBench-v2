@echo off
title Calibrated Audit Dashboard
echo ========================================================
echo Launching Calibrated Audit Demographic Bias Web Dashboard...
echo ========================================================
echo.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else (
    python -m streamlit run app.py
)
pause

