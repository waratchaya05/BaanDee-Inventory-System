@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate
set BAANDEE_AI_MODE=fixture
python -m src.app
