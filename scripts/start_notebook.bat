@echo off
cd /d "%~dp0\.."
call .venv\Scripts\activate
jupyter notebook notebooks\class1_demo.ipynb
