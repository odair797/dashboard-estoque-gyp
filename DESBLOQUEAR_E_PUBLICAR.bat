@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  Removendo trava do git e publicando...
echo ============================================
echo.

echo [1] Removendo index.lock...
if exist ".git\index.lock" (
    del /f ".git\index.lock"
    echo     Removido!
) else (
    echo     Nao encontrado (OK).
)
echo.

echo [2] Adicionando todos os arquivos...
git add -A
git add -f output\Analise_Estoque_GYP.xlsx
echo.

echo [3] Arquivos que serao enviados:
git diff --cached --name-only
echo.

echo [4] Commit...
git commit -m "Exportar Excel funcionando + dashboard atualizado"
echo.

echo [5] Push para GitHub...
git push origin main
if %errorlevel% neq 0 (
    git push origin main --force
)
echo.

echo [6] Status final:
git log --oneline -3
echo.
echo PRONTO! Aguarde 1-2 min e acesse:
echo https://odair797.github.io/dashboard-estoque-gyp/Dashboard_Estoque_GYP.html
echo.
pause
