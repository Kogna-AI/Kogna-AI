@echo off
echo Starting Kogna-AI Backend Server...
echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
