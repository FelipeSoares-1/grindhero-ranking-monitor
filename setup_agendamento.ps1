# setup_agendamento.ps1
# Configura tarefa agendada no Windows para coleta diária às 00:00

$NomeTarefa = "GrindHero_Ranking_Coleta"
$Descricao  = "Coleta diária de dados de ranking do GrindHero Online às meia-noite"

# Caminho do projeto
$PastaBase  = "C:\Users\FelipeSoares\OneDrive - Grupo Dreamers\Documentos\Monitoramento de Ranking"
$ScriptPy   = Join-Path $PastaBase "coletor_ranking.py"
$DashboardPy = Join-Path $PastaBase "gerar_dashboard.py"
$LogDir     = Join-Path $PastaBase "logs"

# Criar pasta de logs se não existir
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Encontrar Python
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Error "Python não encontrado no PATH. Instale o Python primeiro."
    exit 1
}
Write-Host "Python: $PythonPath"

# Remover tarefa existente se houver
Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false -ErrorAction SilentlyContinue

# Criar script bat wrapper (para capturar saída em log)
$BatContent = @"
@echo off
set LOGFILE=%~dp0logs\execucao_%date:~6,4%%date:~3,2%%date:~0,2%.log
echo === Inicio: %date% %time% === >> "%LOGFILE%"
"$PythonPath" "$ScriptPy" >> "%LOGFILE%" 2>&1
echo === Dashboard: %date% %time% === >> "%LOGFILE%"
"$PythonPath" "$DashboardPy" >> "%LOGFILE%" 2>&1
echo === Fim: %date% %time% === >> "%LOGFILE%"
"@
$BatPath = Join-Path $PastaBase "executar_coleta.bat"
$BatContent | Out-File -FilePath $BatPath -Encoding ASCII
Write-Host "Bat criado: $BatPath"

# Configurar ação
$Acao = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatPath`"" `
    -WorkingDirectory $PastaBase

# Gatilho: todo dia às 00:00
$Gatilho = New-ScheduledTaskTrigger -Daily -At "00:00"

# Configurações
$Configuracoes = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Principal (usuário atual)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Registrar tarefa
$Tarefa = Register-ScheduledTask `
    -TaskName $NomeTarefa `
    -Description $Descricao `
    -Action $Acao `
    -Trigger $Gatilho `
    -Settings $Configuracoes `
    -Principal $Principal

if ($Tarefa) {
    Write-Host ""
    Write-Host "✅ Tarefa agendada com sucesso!" -ForegroundColor Green
    Write-Host "   Nome:     $NomeTarefa"
    Write-Host "   Execucao: Diariamente as 00:00"
    Write-Host "   Script:   $ScriptPy"
    Write-Host "   Logs:     $LogDir"
    Write-Host ""
    Write-Host "Para ver a tarefa: Pesquise 'Agendador de Tarefas' no Windows"
    Write-Host "Para executar agora (teste): Start-ScheduledTask -TaskName '$NomeTarefa'"
} else {
    Write-Error "Falha ao criar tarefa agendada."
}
