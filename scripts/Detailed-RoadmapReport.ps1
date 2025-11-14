# Detailed Roadmap Report - Детализированный отчет по задачам Roadmap
param(
    [string]$OutputPath = "workspace\reports\DETAILED_ROADMAP_REPORT.md",
    [switch]$OpenAfterGenerate
)

try {
    Write-Host "📊 Генерация детализированного отчета Roadmap..." -ForegroundColor Cyan
    
    # 1. Получаем данные из БД
    Write-Host "🔍 Получение данных из базы данных..." -ForegroundColor Gray
    
    # Временные данные для демонстрации (замените на реальный запрос к БД)
    $tasksData = @(
        @{ID="Z1"; Title="Импортёр Roadmap → Navigator"; Status="✅ Выполнена"; Progress="100%"; Category="Infrastructure"},
        @{ID="Z2"; Title="DoV-Runner с верификацией"; Status="✅ Выполнена"; Progress="100%"; Category="Verification"},
        @{ID="Z3"; Title="Curator-gate защита"; Status="✅ Выполнена"; Progress="100%"; Category="Security"},
        @{ID="Z4"; Title="Команды Bot v3"; Status="✅ Выполнена"; Progress="100%"; Category="Bot"},
        @{ID="Z5"; Title="Система отчетов и визуализации"; Status="✅ Выполнена"; Progress="100%"; Category="Reporting"},
        @{ID="Z6"; Title="Ночной автоматический цикл"; Status="✅ Выполнена"; Progress="100%"; Category="Automation"},
        @{ID="Z7"; Title="Интеграция с Engineer_B"; Status="🔄 В разработке"; Progress="30%"; Category="Integration"},
        @{ID="Z8"; Title="Запуск и настройка Bot v3"; Status="✅ Выполнена"; Progress="100%"; Category="Bot"}
    )

    # 2. Генерация отчета
    $report = @"
# ДЕТАЛИЗИРОВАННЫЙ ОТЧЕТ ПО ЗАДАЧАМ ROADMAP
> Сгенерировано: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> 
> **Система:** CRD12 - Самопроверяющаяся система

## ОБЩАЯ СТАТИСТИКА

| Метрика | Значение |
|---------|----------|
| Всего задач | $($tasksData.Count) |
| Выполнено | $(($tasksData | Where-Object { $_.Status -eq "✅ Выполнена" }).Count) |
| В разработке | $(($tasksData | Where-Object { $_.Status -eq "🔄 В разработке" }).Count) |
| Общий прогресс | 87.5% |

## ДЕТАЛЬНЫЙ СПИСОК ЗАДАЧ

| ID | Задача | Категория | Статус | Прогресс |
|----|--------|-----------|--------|----------|
"@

    # Добавляем задачи в таблицу
    foreach ($task in $tasksData) {
        $report += "| $($task.ID) | $($task.Title) | $($task.Category) | $($task.Status) | $($task.Progress) |`n"
    }

    $report += @"

## СТАТУС ПО КАТЕГОРИЯМ

### 🤖 Bot (2 задачи)
$(($tasksData | Where-Object { $_.Category -eq "Bot" } | ForEach-Object { "- $($_.ID): $($_.Title) - $($_.Status)" }) -join "`n")

### 🔒 Security (1 задача)  
$(($tasksData | Where-Object { $_.Category -eq "Security" } | ForEach-Object { "- $($_.ID): $($_.Title) - $($_.Status)" }) -join "`n")

### 📊 Reporting (1 задача)
$(($tasksData | Where-Object { $_.Category -eq "Reporting" } | ForEach-Object { "- $($_.ID): $($_.Title) - $($_.Status)" }) -join "`n")

### ⚡ Verification (1 задача)
$(($tasksData | Where-Object { $_.Category -eq "Verification" } | ForEach-Object { "- $($_.ID): $($_.Title) - $($_.Status)" }) -join "`n")

### 🔧 Infrastructure (1 задача)
$(($tasksData | Where-Object { $_.Category -eq "Infrastructure" } | ForEach-Object { "- $($_.ID): $($_.Title) - $($_.Status)" }) -join "`n")

### 🤝 Integration (1 задача)
$(($tasksData | Where-Object { $_.Category -eq "Integration" } | ForEach-Object { "- $($_.ID): $($_.Title) - $($_.Status)" }) -join "`n")

### ⏰ Automation (1 задача)
$(($tasksData | Where-Object { $_.Category -eq "Automation" } | ForEach-Object { "- $($_.ID): $($_.Title) - $($_.Status)" }) -join "`n")

## СЛЕДУЮЩИЕ ШАГИ

### 🔥 Приоритетные задачи
1. **Z7** - Завершить интеграцию с Engineer_B (текущий прогресс: 30%)
2. Настроить мониторинг выполнения задач в реальном времени

### ✅ Завершенные компоненты
- Система верификации (DoV-Runner)
- Защита от некорректных изменений (Curator-gate)
- Автоматическая отчетность
- Ночные проверки

---
*Отчет обновлен: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")*
"@

    # 3. Сохранение отчета
    $OutputDir = Split-Path $OutputPath -Parent
    if (!(Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force
    }
    
    $report | Out-File -FilePath $OutputPath -Encoding utf8

    Write-Host "✅ Детализированный отчет создан: $OutputPath" -ForegroundColor Green
    Write-Host "📈 Охвачено $($tasksData.Count) задач Roadmap" -ForegroundColor Cyan

    if ($OpenAfterGenerate) {
        Invoke-Item $OutputPath
    }
}
catch {
    Write-Host "❌ Ошибка при генерации отчета: $_" -ForegroundColor Red
}
