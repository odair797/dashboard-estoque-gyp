@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  Regenerando Dashboard do zero...
echo ============================================
echo.

python atualizar.py

if %errorlevel%==0 (
    echo.
    echo ============================================
    echo  PRONTO! Dashboard regenerado e limpo.
    echo  Abra o Dashboard_Estoque_GYP.html e teste.
    echo ============================================
) else (
    echo.
    echo [ERRO] Verifique se há arquivo .tsv na pasta input\
)

pause
