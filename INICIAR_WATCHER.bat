@echo off
chcp 65001 >nul
title Watcher YBERA - Saldo de Estoque
cd /d "%~dp0"
color 0E

where python >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado. Instale em: https://python.org/downloads/
    pause
    exit /b 1
)

python watcher.py

echo.
echo Watcher encerrado.
pause
