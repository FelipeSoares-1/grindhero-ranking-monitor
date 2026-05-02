@echo off
title GrindHero - Coleta de Ranking

:: Diretorio do projeto (onde este .bat esta localizado)
set PROJECT_DIR=%~dp0
set LOGFILE=%PROJECT_DIR%logs\execucao_%date:~6,4%%date:~3,2%%date:~0,2%.log

:: Criar pasta de logs se nao existir
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

:: Detectar Python no PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Python nao encontrado no PATH. Instale o Python e tente novamente.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   GrindHero Monitor - Coleta de Ranking
echo ============================================================
echo.
echo [%time%] Iniciando coleta... Aguarde, pode levar ate 5 minutos.
echo.

echo === Inicio: %date% %time% === >> "%LOGFILE%"

powershell -NoProfile -Command "python -u '%PROJECT_DIR%coletor_ranking.py' 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"

echo.
echo [%time%] Gerando dashboard...
echo === Dashboard: %date% %time% === >> "%LOGFILE%"

powershell -NoProfile -Command "python -u '%PROJECT_DIR%gerar_dashboard.py' 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"

echo === Fim: %date% %time% === >> "%LOGFILE%"

echo.
echo ============================================================
echo   Concluido! Pressione qualquer tecla para fechar.
echo ============================================================
pause
