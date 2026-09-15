@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting AI Card Alchemy on http://127.0.0.1:8796 ...
start "" http://127.0.0.1:8796
set "PY="
where python  >nul 2>nul && set "PY=python"
if not defined PY (where py >nul 2>nul && set "PY=py")
if not defined PY (where python3 >nul 2>nul && set "PY=python3")
if not defined PY (
  echo 没有找到 Python，请先安装 Python 3.10+ 并加入 PATH。
  pause
  exit /b 1
)
%PY% scripts\studio_server.py
pause
