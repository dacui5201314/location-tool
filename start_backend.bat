@echo off
cd /d "%~dp0backend"
echo [Hermes] Starting backend from %cd%
echo [Hermes] Working directory must be backend/ for imports (models, prompts, services)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
