@echo off
:: Versao silenciosa para o Agendador (sem pause no final)
title GrindHero - Coleta Automatica

set PROJECT_DIR=%~dp0
set LOGFILE=%PROJECT_DIR%logs\execucao_%date:~6,4%%date:~3,2%%date:~0,2%.log

if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH. >> "%LOGFILE%"
    exit /b 1
)

echo === Inicio: %date% %time% === >> "%LOGFILE%"
python -u "%PROJECT_DIR%coletor_ranking.py" >> "%LOGFILE%" 2>&1

echo === Dashboard: %date% %time% === >> "%LOGFILE%"
python -u "%PROJECT_DIR%gerar_dashboard.py" >> "%LOGFILE%" 2>&1

echo === Fim: %date% %time% === >> "%LOGFILE%"
exit /b 0
