@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title YBERA GROUP - Subir Dashboard
cd /d "%~dp0"
color 0E
cls

echo.
echo ================================================================
echo   YBERA GROUP  -  ATUALIZAR / PUBLICAR / ABRIR NO CHROME
echo ================================================================
echo.

REM ==== Verificacoes ====
where python >nul 2>&1
if errorlevel 1 ( color 0C & echo [ERRO] Python nao encontrado. Instale em https://python.org/downloads/ & echo. & pause & exit /b 1 )
where git >nul 2>&1
if errorlevel 1 ( color 0C & echo [ERRO] Git nao encontrado. Rode INSTALAR_GIT.bat. & echo. & pause & exit /b 1 )

set "TSV_FILE="

REM ==== 1) Arquivo arrastado para o .bat ====
if not "%~1"=="" (
    set "TSV_FILE=%~1"
    echo  [1/4] TSV arrastado: %~nx1
    goto :tem_tsv
)

REM ==== 2) Sem arrastar: procurar TSV mais recente em Downloads ====
echo  [1/4] Nenhum arquivo arrastado. Procurando TSV mais recente...
set "DLF=%USERPROFILE%\Downloads"
for /f "delims=" %%I in ('dir /b /a-d /o-d "%DLF%\*.tsv" 2^>nul') do ( set "TSV_FILE=%DLF%\%%I" & goto :tem_tsv )

REM ==== 3) Senao, usar o que ja existe em input\ ====
for /f "delims=" %%I in ('dir /b /a-d /o-d "%~dp0input\*.tsv" 2^>nul') do (
    echo        Usando TSV ja presente em input\: %%I
    goto :processar
)

color 0C
echo.
echo  [!] Nenhum arquivo .tsv encontrado.
echo      Baixe o TSV de Saldo de Estoque do Senior (vai para Downloads)
echo      e rode este arquivo de novo. Ou arraste o .tsv sobre este icone.
echo.
pause & exit /b 1

:tem_tsv
if not exist "!TSV_FILE!" ( color 0C & echo  [ERRO] Arquivo nao encontrado: !TSV_FILE! & echo. & pause & exit /b 1 )
echo        Origem: !TSV_FILE!
echo        Limpando TSVs antigos de input\ ...
del /Q "%~dp0input\*.tsv" >nul 2>&1
del /Q "%~dp0input\*.txt"  >nul 2>&1
copy /Y "!TSV_FILE!" "%~dp0input\" >nul
if errorlevel 1 ( color 0C & echo [ERRO] Falha ao copiar para input\. & echo. & pause & exit /b 1 )
echo        OK.

:processar
echo.
echo  [2/4] Processando dados e atualizando dashboard...
echo.
python atualizar.py
if errorlevel 1 ( color 0C & echo. & echo [ERRO] Processamento falhou. Veja a mensagem acima. & echo. & pause & exit /b 1 )

echo.
echo  [3/4] Publicando no GitHub e abrindo no Chrome...
echo.
python publicar.py
if errorlevel 1 ( color 0C & echo. & echo [ERRO] Publicacao falhou. Veja a mensagem acima. & echo. & pause & exit /b 1 )

echo.
color 0A
echo ================================================================
echo   [4/4] PUBLICADO  -  %DATE%  %TIME%
echo ================================================================
echo.
echo  Esta janela fecha em 15 segundos.
timeout /t 15 >nul
endlocal
exit /b 0
