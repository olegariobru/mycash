@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python scripts\download_fonts.py
python -m PyInstaller --noconfirm --clean --onefile --windowed --add-data "assets;assets" --name "mycash" desktop.py
echo.
echo Executavel criado em: dist\mycash.exe
pause

