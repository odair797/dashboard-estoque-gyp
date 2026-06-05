@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  DIAGNOSTICO GIT + PUSH FORCADO
echo ============================================
echo.

echo [STATUS DO GIT]
git status
echo.

echo [COMMITS PENDENTES]
git log --oneline -5
echo.

echo [ADICIONANDO ARQUIVOS]
git add -A
git add -f output\Analise_Estoque_GYP.xlsx
echo.

echo [VERIFICANDO O QUE SERA ENVIADO]
git diff --cached --name-only
echo.

echo [COMMIT]
git commit -m "Atualiza dashboard: exportar Excel + remove badge ref"
echo.

echo [PUSH]
git push origin main
if %errorlevel% neq 0 (
    echo Tentando force push...
    git push origin main --force
)
echo.

echo [RESULTADO FINAL]
git log --oneline -3
echo.
echo Link: https://odair797.github.io/dashboard-estoque-gyp/Dashboard_Estoque_GYP.html
echo.
pause
