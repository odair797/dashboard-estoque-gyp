@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title YBERA GROUP - Subir Dashboard (arraste o TSV aqui)
cd /d "%~dp0"
color 0E
cls

echo.
echo ================================================================
echo   YBERA GROUP  -  ARRASTE O TSV PARA PUBLICAR O DASHBOARD
echo ================================================================
echo.

if "%~1"=="" (
    color 0C
    echo  [!] Nenhum arquivo foi arrastado.
    echo.
    echo  COMO USAR:
    echo    1) Baixe o TSV de Saldo de Estoque do Senior.
    echo    2) ARRASTE o arquivo .tsv e SOLTE em cima do icone
    echo       deste arquivo ^(SUBIR_DASHBOARD.bat^).
    echo.
    echo  Dica: crie um atalho na Area de Trabalho para facilitar.
    echo.
    pause
    exit /b 1
)

set "TSV_FILE=%~1"
echo  [1/4] Arquivo recebido: %~nx1

if not exist "!TSV_FILE!" ( color 0C & echo  [ERRO] Arquivo nao encontrado: !TSV_FILE! & pause & exit /b 1 )

where python >nul 2>&1
if errorlevel 1 ( color 0C & echo [ERRO] Python nao encontrado. Instale em https://python.org/downloads/ & pause & exit /b 1 )
where git >nul 2>&1
if errorlevel 1 ( color 0C & echo [ERRO] Git nao encontrado. Rode INSTALAR_GIT.bat. & pause & exit /b 1 )

REM ---- Limpar TSVs antigos e copiar o novo ----
echo        Limpando TSVs antigos de input\ ...
del /Q "%~dp0input\*.tsv" >nul 2>&1
del /Q "%~dp0input\*.txt"  >nul 2>&1
copy /Y "!TSV_FILE!" "%~dp0input\" >nul
if errorlevel 1 ( color 0C & echo [ERRO] Falha ao copiar para input\. & pause & exit /b 1 )
echo        OK.

REM ---- Processar (Excel + Dashboard) ----
echo.
echo  [2/4] Processando dados e atualizando dashboard...
echo.
python atualizar.py
if errorlevel 1 ( color 0C & echo. & echo [ERRO] Processamento falhou. Veja a mensagem acima. & pause & exit /b 1 )

REM ---- Publicar no GitHub + abrir no Chrome (URL automatica) ----
echo.
echo  [3/4] Publicando no GitHub e gerando link automatico...
echo.
python publicar.py
if errorlevel 1 ( color 0C & echo. & echo [ERRO] Publicacao falhou. Veja a mensagem acima. & pause & exit /b 1 )

echo.
echo  [4/4] Concluido.
color 0A
echo ================================================================
echo   PUBLICADO  -  %DATE%  %TIME%
echo ================================================================
timeout /t 10 >nul
endlocal
exit /b 0
