@echo off
chcp 65001 >nul
title Atualizar Dashboard - YBERA GROUP
cd /d "%~dp0"
color 0E

echo.
echo ════════════════════════════════════════════════════════════════
echo   ATUALIZAR DASHBOARD - YBERA GROUP / Saldo de Estoque
echo ════════════════════════════════════════════════════════════════
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale em: https://python.org/downloads/
    pause
    exit /b 1
)

REM ── MODO 1: Arquivo arrastado para o .bat ────────────────────
if not "%~1"=="" (
    echo  Arquivo recebido: %~nx1
    echo.
    set "TSV_FILE=%~1"
    goto :copiar
)

REM ── MODO 2: Perguntar o caminho ───────────────────────────────
echo  Cole o CAMINHO COMPLETO do arquivo .tsv baixado do Senior
echo  ^(ou simplesmente arraste o arquivo aqui na janela^)
echo.
echo  Exemplo: C:\Users\pc\Downloads\Exportacao_2026.tsv
echo.
echo  ─ ENTER em branco usa o .tsv mais recente em input/ ou Downloads
echo.
set /p TSV_FILE="  TSV: "

REM Remover aspas se o usuario colou com elas
set TSV_FILE=%TSV_FILE:"=%

if "%TSV_FILE%"=="" (
    echo.
    echo  Sem caminho informado. Procurando .tsv mais recente...
    goto :rodar_padrao
)

:copiar
if not exist "%TSV_FILE%" (
    echo.
    echo  [ERRO] Arquivo nao encontrado: %TSV_FILE%
    echo.
    pause
    exit /b 1
)

echo.
echo  ─── Copiando para input/ ───
copy /Y "%TSV_FILE%" "%~dp0input\" >nul
if errorlevel 1 (
    echo  [ERRO] Falha ao copiar.
    pause
    exit /b 1
)
echo  ✓ Arquivo copiado.
echo.

:rodar_padrao
echo  ─── Processando ───
echo.
python atualizar.py
set RC=%ERRORLEVEL%

echo.
echo ════════════════════════════════════════════════════════════════
if %RC%==0 (
    color 0A
    echo   ✅ ATUALIZACAO CONCLUIDA
    echo.
    echo   📊 Excel    : output\Analise_Estoque_GYP.xlsx
    echo   🌐 Dashboard: Dashboard_Estoque_GYP.html
    echo.
    set /p ABRIR="  Abrir o Dashboard agora? (S/N): "
    if /i "%ABRIR%"=="S" start "" "Dashboard_Estoque_GYP.html"
) else (
    color 0C
    echo   ❌ ERRO durante a atualizacao
    echo   Veja a mensagem acima.
)
echo ════════════════════════════════════════════════════════════════
echo.
pause
