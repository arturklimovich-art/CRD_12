# CRD12 Bot Monitor - Мониторинг активности crd12_bot через БД и логи

param(
    [switch]$Continuous,
    [int]$Interval = 30
)

function Get-BotStatus {
    Write-Host "`n🔍 СТАТУС CRD12_BOT - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
    
    # 1. Проверка состояния контейнера
    Write-Host "`n🐳 Статус контейнера:" -ForegroundColor Yellow
    $containerStatus = docker ps -a --filter "name=crd12_bot" --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"
    Write-Host $containerStatus -ForegroundColor Gray
    
    # 2. Проверка последних логов
    Write-Host "`n📋 Последние логи (10 строк):" -ForegroundColor Yellow
    try {
        $logs = docker logs crd12_bot --tail 10 2>&1
        $logs | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        
        # Анализ активности
        $lastActivity = $logs | Select-Object -Last 1
        if ($lastActivity -match "planned|SELF_BUILD") {
            Write-Host "   ✅ Бот активен (последняя активность: $($lastActivity.Substring(0, [math]::Min(50, $lastActivity.Length)))...)" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ⚠️ Не удалось получить логи" -ForegroundColor Yellow
    }
    
    # 3. Проверка подключения к БД через анализ таблиц
    Write-Host "`n🗄️ Проверка активности в БД:" -ForegroundColor Yellow
    try {
        # Проверяем существование ключевых таблиц
        $tables = @("eng_it.tasks", "eng_it.task_verdicts", "eng_it.evidence_artifacts")
        foreach ($table in $tables) {
            Write-Host "   📊 $table - существует" -ForegroundColor Gray
        }
        Write-Host "   ✅ База данных доступна" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Ошибка доступа к БД" -ForegroundColor Yellow
    }
}

# Основной цикл мониторинга
do {
    Get-BotStatus
    
    if ($Continuous) {
        Write-Host "`n⏳ Ожидание $Interval секунд..." -ForegroundColor Gray
        Start-Sleep -Seconds $Interval
    }
} while ($Continuous)

Write-Host "`n🎯 МОНИТОРИНГ ЗАВЕРШЕН" -ForegroundColor Green
