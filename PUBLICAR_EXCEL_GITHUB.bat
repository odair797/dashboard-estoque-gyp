@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  Publicando Excel + Dashboard no GitHub
echo ============================================
echo.

echo [1/4] Adicionando .gitignore...
git add .gitignore
echo.

echo [2/4] Forcando adicao do Excel...
git add -f output\Analise_Estoque_GYP.xlsx
echo.

echo [3/4] Adicionando restante dos arquivos...
git add -A
echo.

echo [4/4] Status atual:
git status
echo.

git diff --cached --name-only
echo.

git commit -m "Publica Excel e remove badge de referencia"
echo.

echo Enviando para GitHub...
git push -u origin main
if %errorlevel% neq 0 (
    echo Tentando com force...
    git push -u origin main --force
)

echo.
if %errorlevel%==0 (
    echo ============================================
    echo  PRONTO! Publicado com sucesso.
    echo  Excel: https://github.com/odair797/dashboard-estoque-gyp/raw/main/output/Analise_Estoque_GYP.xlsx
    echo ============================================
) else (
    echo [ERRO] Push falhou. Veja o erro acima.
)

pause
