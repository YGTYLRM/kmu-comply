@echo off
set PATH=%USERPROFILE%\scoop\apps\postgresql\current\bin;%PATH%
cd /d "%~dp0\.."
"C:\Python314\python.exe" "%~dp0backup_nightly.py"
