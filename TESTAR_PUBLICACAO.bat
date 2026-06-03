@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM Copia um TSV de exemplo para fora de input\ e chama o fluxo real
copy /Y "input\Exportacao_1780417710752.tsv" "%TEMP%\teste_saldo_estoque.tsv" >nul
call "%~dp0SUBIR_DASHBOARD.bat" "%TEMP%\teste_saldo_estoque.tsv"
