@echo off
chcp 65001 >nul
cd /d "%~dp0"
title YBERA - Publicar agora no GitHub
color 0E
echo ================================================================
echo   PUBLICANDO O DASHBOARD ATUAL NO GITHUB
echo ================================================================
echo.
python publicar.py
echo.
echo ================================================================
echo  Concluido. (Se aparecer janela de login do GitHub, conclua o
echo  login UMA vez; depois publica sozinho sempre.)
echo ================================================================
timeout /t 30 >nul
