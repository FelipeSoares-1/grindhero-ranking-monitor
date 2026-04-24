@echo off
title GrindHero - Coleta de Ranking
set LOGFILE=%~dp0logs\execucao_%date:~6,4%%date:~3,2%%date:~0,2%.log

echo.
echo ============================================================
echo   GrindHero Monitor - Coleta de Ranking
echo ============================================================
echo.
echo [%time%] Iniciando coleta... Aguarde, pode levar ate 5 minutos.
echo.

echo === Inicio: %date% %time% === >> "%LOGFILE%"

powershell -NoProfile -Command "& 'C:\Python314\python.exe' -u 'C:\Users\FelipeSoares\OneDrive - Grupo Dreamers\Documentos\Monitoramento de Ranking\coletor_ranking.py' 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"

echo.
echo [%time%] Gerando dashboard...
echo === Dashboard: %date% %time% === >> "%LOGFILE%"

powershell -NoProfile -Command "& 'C:\Python314\python.exe' -u 'C:\Users\FelipeSoares\OneDrive - Grupo Dreamers\Documentos\Monitoramento de Ranking\gerar_dashboard.py' 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"

echo === Fim: %date% %time% === >> "%LOGFILE%"

echo.
echo ============================================================
echo   Concluido! Pressione qualquer tecla para fechar.
echo ============================================================
pause
