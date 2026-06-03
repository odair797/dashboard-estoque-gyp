@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title YBERA GROUP - Subir Dashboard
cd /d "%~dp0"
color 0E
cls

echo.
echo ================================================================
echo   YBERA GROUP  -  ATUALIZAR E PUBLICAR O DASHBOARD
echo ================================================================
echo.

REM ==== Verificacoes ====
where python >nul 2>&1
if errorlevel 1 ( color 0C & echo [ERRO] Python nao encontrado. Instale em https://python.org/downloads/ & echo. & pause & exit /b 1 )
where git >nul 2>&1
if errorlevel 1 ( color 0C & echo [ERRO] Git nao encontrado. Rode INSTALAR_GIT.bat. & echo. & pause & exit /b 1 )

set "TSV_FILE="

REM ==== Se arrastou direto no icone do .bat, ja usa ====
if not "%~1"=="" (
    set "TSV_FILE=%~1"
    echo  TSV recebido: %~nx1
    goto :tem_tsv
)

REM ==== Modo interativo: arrastar o arquivo para DENTRO desta janela ====
echo  PASSO UNICO:
echo    1) ARRASTE o arquivo .tsv para DENTRO desta janela preta
echo    2) Tecle ENTER
echo.
set /p "TSV_FILE=  Arraste o TSV aqui e tecle ENTER: "

REM Remove aspas que o Windows adiciona ao arrastar
set "TSV_FILE=!TSV_FILE:"=!"

if not defined TSV_FILE goto :sem_arquivo
if "!TSV_FILE!"=="" goto :sem_arquivo
goto :tem_tsv

:sem_arquivo
color 0C
echo.
echo  [!] Nenhum arquivo informado.
echo      Arraste o .tsv para dentro da janela antes de teclar ENTER.
echo.
pause & exit /b 1

:tem_tsv
if not exist "!TSV_FILE!" ( color 0C & echo. & echo  [ERRO] Arquivo nao encontrado: !TSV_FILE! & echo. & pause & exit /b 1 )
echo.
echo  [1/3] Arquivo: !TSV_FILE!
echo        Atualizando input\ ...
del /Q "%~dp0input\*.tsv" >nul 2>&1
del /Q "%~dp0input\*.txt"  >nul 2>&1
copy /Y "!TSV_FILE!" "%~dp0input\" >nul
if errorlevel 1 ( color 0C & echo  [ERRO] Falha ao copiar para input\. & echo. & pause & exit /b 1 )
echo        OK.

echo.
echo  [2/3] Processando dados e atualizando dashboard...
echo.
python atualizar.py
if errorlevel 1 ( color 0C & echo. & echo  [ERRO] Processamento falhou. Veja acima. & echo. & pause & exit /b 1 )

echo.
echo  [3/3] Publicando no GitHub e abrindo no Chrome...
echo.
python publicar.py
if errorlevel 1 ( color 0C & echo. & echo  [ERRO] Publicacao falhou. Veja acima. & echo. & pause & exit /b 1 )

echo.
color 0A
echo ================================================================
echo   PUBLICADO  -  %DATE%  %TIME%
echo ================================================================
echo.
echo  Esta janela fecha em 15 segundos.
timeout /t 15 >nul
endlocal
exit /b 0
