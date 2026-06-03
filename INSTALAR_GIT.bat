@echo off
setlocal enabledelayedexpansion
title Instalar Git automaticamente
color 0E
cls

echo.
echo ================================================================
echo   INSTALADOR AUTOMATICO DO GIT
echo ================================================================
echo.

REM ---- Verificar se Git ja esta instalado ----
where git >nul 2>&1
if not errorlevel 1 (
    color 0A
    echo  Git ja esta instalado!
    git --version
    echo.
    echo  Pode fechar esta janela e usar PUBLICAR_NO_GITHUB.bat
    echo.
    pause
    exit /b 0
)

echo  Git NAO esta instalado. Vou instalar agora.
echo.

REM ---- Tentar winget primeiro (Windows 10/11) ----
where winget >nul 2>&1
if not errorlevel 1 (
    echo  Usando o gerenciador de pacotes do Windows ^(winget^)...
    echo.
    echo  ATENCAO: Pode aparecer um popup do Windows pedindo permissao.
    echo           Clique em "Sim" para autorizar a instalacao.
    echo.
    echo  Aguarde - pode levar 1-2 minutos...
    echo.
    winget install --id Git.Git -e --silent --accept-source-agreements --accept-package-agreements

    REM Atualizar PATH na sessao atual
    set "PATH=%PATH%;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"

    where git >nul 2>&1
    if not errorlevel 1 (
        color 0A
        echo.
        echo ================================================================
        echo   GIT INSTALADO COM SUCESSO!
        echo ================================================================
        git --version
        echo.
        echo  Agora:
        echo    1. FECHE esta janela
        echo    2. FECHE qualquer outra janela de CMD que estiver aberta
        echo    3. Volte e arraste o TSV no PUBLICAR_NO_GITHUB.bat
        echo.
        pause
        exit /b 0
    )

    echo  Winget terminou mas o Git ainda nao foi detectado.
    echo  Pode precisar reiniciar o terminal. Tentando outra abordagem...
    echo.
)

REM ---- Fallback: baixar e rodar o instalador manualmente ----
echo  Abordagem alternativa: baixar o instalador do site oficial.
echo.
set "INSTALLER=%TEMP%\GitInstaller.exe"

echo  Baixando Git Installer ^(aproximadamente 60 MB^)...
echo.
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/Git-2.45.2-64-bit.exe' -OutFile '%INSTALLER%'" 2>nul

if not exist "%INSTALLER%" (
    color 0C
    echo  [ERRO] Falha no download automatico.
    echo.
    echo  Vou abrir a pagina para voce baixar manualmente:
    start "" "https://git-scm.com/download/win"
    echo.
    pause
    exit /b 1
)

echo.
echo  Download OK. Iniciando instalacao silenciosa...
echo  ATENCAO: pode aparecer um popup de permissao - clique "Sim".
echo.
"%INSTALLER%" /VERYSILENT /NORESTART /COMPONENTS="gitlfs,assoc,assoc_sh,scalar"

REM Atualizar PATH e verificar
set "PATH=%PATH%;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"

timeout /t 3 >nul
where git >nul 2>&1
if not errorlevel 1 (
    color 0A
    echo.
    echo ================================================================
    echo   GIT INSTALADO COM SUCESSO!
    echo ================================================================
    git --version
    echo.
    echo  FECHE esta janela e qualquer outra de CMD aberta.
    echo  Depois arraste o TSV no PUBLICAR_NO_GITHUB.bat.
    echo.
) else (
    color 0C
    echo.
    echo  Instalacao concluida, mas Git ainda nao detectado nesta sessao.
    echo  Reinicie o computador e tente o PUBLICAR_NO_GITHUB.bat de novo.
    echo.
)

pause
exit /b 0
