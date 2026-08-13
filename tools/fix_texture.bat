@echo off
setlocal

if "%~1"=="" (
  echo Drag one PNG file onto this script.
  pause
  exit /b 1
)

python "%~dp0build_pack.py" "%~1"
if errorlevel 1 pause
