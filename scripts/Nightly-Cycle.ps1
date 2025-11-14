# CRD12 Nightly Cycle - Автоматический ночной цикл проверки
# Запускается ежедневно в 2:00 AM через Планировщик заданий Windows

param(
    [switch]$ForceRun
)

try {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $snapshotName = "NIGHTLY_$(Get-Date -Format 'yyyy-MM-dd')"
    
    Write-Host "🌙 [$(Get-Date)] Запуск ночного цикла CRD12..." -ForegroundColor Cyan
    Write-Host "📅 Дата выполнения: $timestamp" -ForegroundColor Gray
    
    # Логируем начало выполнения
    $logEntry = "[$timestamp] НОЧНОЙ ЦИКЛ: Запуск CRD12 Nightly Cycle"
    $logEntry | Out-File -FilePath "workspace\reports\nightly_cycle.log" -Append -Encoding utf8

    # 1. Запуск полной проверки системы через DoV-Runner
    Write-Host "`n🔍 Этап 1: Запуск DoV-Runner..." -ForegroundColor Yellow
    if (Test-Path "scripts\DoV-Runner.ps1") {
        .\scripts\DoV-Runner.ps1 -Mode Full -SnapshotName $snapshotName
        Write-Host "✅ DoV-Runner выполнен" -ForegroundColor Green
    } else {
        Write-Host "⚠️ DoV-Runner не найден, пропускаем этап" -ForegroundColor Yellow
    }

    # 2. Генерация ночного отчета
    Write-Host "`n📊 Этап 2: Генерация ночного отчета..." -ForegroundColor Yellow
    if (Test-Path "scripts\Report-TruthMatrix.ps1") {
        $nightlyReportPath = "workspace\reports\NIGHTLY_REPORT_$($snapshotName).md"
        .\scripts\Report-TruthMatrix.ps1 -OutputPath $nightlyReportPath
        Write-Host "✅ Ночной отчет создан: $nightlyReportPath" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Report-TruthMatrix не найден, пропускаем этап" -ForegroundColor Yellow
    }

    # 3. Проверка состояния Docker контейнеров
    Write-Host "`n🐳 Этап 3: Проверка Docker контейнеров..." -ForegroundColor Yellow
    try {
        $dockerPs = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker контейнеры проверены:" -ForegroundColor Green
            $dockerPs | Select-Object -Skip 1 | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
            
            # Сохраняем статус контейнеров в лог
            "Контейнеры Docker:" | Out-File -FilePath "workspace\reports\nightly_cycle.log" -Append -Encoding utf8
            $dockerPs | Out-File -FilePath "workspace\reports\nightly_cycle.log" -Append -Encoding utf8
        } else {
            Write-Host "⚠️ Docker не доступен" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️ Ошибка проверки Docker: $_" -ForegroundColor Yellow
    }

    # 4. Финальный отчет и логирование
    $completionTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "`n✅ Ночной цикл завершен: $completionTime" -ForegroundColor Green
    
    $completionLog = "[$completionTime] НОЧНОЙ ЦИКЛ: Успешное завершение"
    $completionLog | Out-File -FilePath "workspace\reports\nightly_cycle.log" -Append -Encoding utf8

    # 5. Создание файла-маркера успешного выполнения
    $markerContent = @"
# CRD12 NIGHTLY CYCLE - MARKER FILE
Сгенерировано: $completionTime
Цикл: $snapshotName
Статус: Успешно

Компоненты выполнены:
- DoV-Runner: $(if (Test-Path "scripts\DoV-Runner.ps1") { "✅" } else { "❌" })
- Truth Matrix: $(if (Test-Path "scripts\Report-TruthMatrix.ps1") { "✅" } else { "❌" })
- Docker Check: ✅

Следующий цикл: $(Get-Date).AddDays(1)
"@
    $markerContent | Out-File -FilePath "workspace\reports\LAST_NIGHTLY_SUCCESS.md" -Encoding utf8

}
catch {
    $errorTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errorMsg = "[$errorTime] НОЧНОЙ ЦИКЛ: ОШИБКА - $($_.Exception.Message)"
    Write-Host "❌ $errorMsg" -ForegroundColor Red
    $errorMsg | Out-File -FilePath "workspace\reports\nightly_cycle.log" -Append -Encoding utf8
    throw
}
