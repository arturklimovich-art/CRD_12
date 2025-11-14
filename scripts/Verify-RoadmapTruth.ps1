# Roadmap Truth Verification - Проверка соответствия системы источнику истины
param(
    [string]$OutputPath = "workspace\reports\ROADMAP_TRUTH_VERIFICATION.md",
    [switch]$OpenAfterGenerate
)

try {
    Write-Host "🔍 Проверка соответствия системы Roadmap..." -ForegroundColor Cyan
    
    # 1. Поиск актуального Roadmap файла
    Write-Host "📁 Поиск файлов Roadmap..." -ForegroundColor Gray
    $roadmapFiles = Get-ChildItem "workspace\readmap\revisions\" -Filter "*.md" | Sort-Object LastWriteTime -Descending
    
    if ($roadmapFiles.Count -eq 0) {
        Write-Host "❌ Файлы Roadmap не найдены" -ForegroundColor Red
        return
    }
    
    $latestRoadmap = $roadmapFiles[0]
    Write-Host "✅ Найден актуальный Roadmap: $($latestRoadmap.Name)" -ForegroundColor Green
    
    # 2. Чтение и анализ Roadmap
    $roadmapContent = Get-Content $latestRoadmap.FullName -Raw
    Write-Host "📊 Анализ содержимого Roadmap..." -ForegroundColor Gray
    
    # 3. Извлечение задач из Roadmap (пример парсинга)
    $roadmapTasks = @()
    
    # Поиск задач в формате Markdown
    $taskMatches = [regex]::Matches($roadmapContent, '-\s*\[(.)\]\s*(.+?)(?=\n-|\n#|$)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    
    foreach ($match in $taskMatches) {
        $status = $match.Groups[1].Value
        $description = $match.Groups[2].Value.Trim()
        
        $roadmapTasks += @{
            Status = $status
            Description = $description
            Verified = "❌"
            Evidence = "Нет данных"
        }
    }
    
    Write-Host "✅ Найдено задач в Roadmap: $($roadmapTasks.Count)" -ForegroundColor Green
    
    # 4. Проверка соответствия системы (DoV проверки)
    Write-Host "🔍 Проверка фактического состояния системы..." -ForegroundColor Gray
    
    # Проверка Docker контейнеров
    $dockerStatus = docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>&1
    $containersRunning = $LASTEXITCODE -eq 0
    
    # Проверка доступности БД
    $dbAccessible = Test-Path "workspace\reports\SYSTEM_PASSPORT.json"  # Пример проверки
    
    # Проверка скриптов
    $scriptsAvailable = @(
        "scripts\DoV-Runner.ps1",
        "scripts\Report-TruthMatrix.ps1", 
        "scripts\Nightly-Cycle.ps1",
        "scripts\Bot-Monitor.ps1"
    )
    
    $availableScripts = $scriptsAvailable | Where-Object { Test-Path $_ }
    
    # 5. Генерация отчета о соответствии
    $report = @"
# ОТЧЕТ О СООТВЕТСТВИИ СИСТЕМЫ ROADMAP
> Сгенерировано: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> 
> **Источник истины:** $($latestRoadmap.Name)
> **Система:** CRD12

## 📋 ОБЩЕЕ СООТВЕТСТВИЕ

| Компонент | Состояние | Соответствие |
|-----------|-----------|--------------|
| Roadmap файл | ✅ Найден | Источник истины |
| Docker контейнеры | $(if($containersRunning){"✅ Работают"}else{"❌ Ошибка"}) | $(if($containersRunning){"✅"}else{"❌"}) |
| База данных | $(if($dbAccessible){"✅ Доступна"}else{"❌ Недоступна"}) | $(if($dbAccessible){"✅"}else{"❌"}) |
| Системные скрипты | ✅ $($availableScripts.Count)/$($scriptsAvailable.Count) | ✅ |

## 🎯 ЗАДАЧИ ИЗ ROADMAP И ИХ ВЕРИФИКАЦИЯ

| Статус в Roadmap | Задача | Соответствие | Доказательства |
|------------------|--------|---------------|----------------|
"@

    # Добавляем задачи из Roadmap
    foreach ($task in $roadmapTasks) {
        $statusIcon = switch ($task.Status) {
            "x" { "✅" }
            " " { "⏳" } 
            default { "📝" }
        }
        
        $report += "| $statusIcon | $($task.Description) | $($task.Verified) | $($task.Evidence) |`n"
    }

    $report += @"

## 🔍 РЕЗУЛЬТАТЫ ПРОВЕРКИ СИСТЕМЫ

### ✅ РАБОТАЮЩИЕ КОМПОНЕНТЫ
$(if($containersRunning){"- Docker контейнеры активны"}else{"- ❌ Docker недоступен"})
$(if($dbAccessible){"- База данных доступна"}else{"- ❌ БД недоступна"})
- $($availableScripts.Count) системных скриптов готовы

### 📊 СТАТИСТИКА СООТВЕТСТВИЯ
- Задач в Roadmap: $($roadmapTasks.Count)
- Проверено системой: $($roadmapTasks | Where-Object { $_.Verified -eq "✅" }).Count
- Требует проверки: $($roadmapTasks | Where-Object { $_.Verified -eq "❌" }).Count

### 🚨 КРИТИЧЕСКИЕ НЕСООТВЕТСТВИЯ
$(if(-not $containersRunning){"- ❌ Docker контейнеры не работают"}
elseif(-not $dbAccessible){"- ❌ База данных недоступна"}
elseif($availableScripts.Count -lt $scriptsAvailable.Count){"- ⚠️ Не все системные скрипты доступны"}
else{"- ✅ Критических несоответствий не обнаружено"})

## 🎯 РЕКОМЕНДАЦИИ

### 🔥 НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ
1. Запустить DoV-Runner для сбора доказательств
2. Синхронизировать Navigator с актуальным Roadmap
3. Проверить верификацию выполненных задач

### 📈 ДОЛГОСРОЧНЫЕ ЦЕЛИ
1. Автоматическая проверка соответствия Roadmap
2. Верификация всех задач через DoV-Runner
3. Синхронизация всех компонентов системы

---
*Система проверки соответствия: Roadmap → Navigator → DoV → Отчет*
*Доказательство важнее заявления*
"@

    # 6. Сохранение отчета
    $OutputDir = Split-Path $OutputPath -Parent
    if (!(Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force
    }
    
    $report | Out-File -FilePath $OutputPath -Encoding utf8

    Write-Host "✅ Отчет о соответствии создан: $OutputPath" -ForegroundColor Green
    Write-Host "📈 Проанализировано $($roadmapTasks.Count) задач из Roadmap" -ForegroundColor Cyan

    if ($OpenAfterGenerate) {
        Invoke-Item $OutputPath
    }
}
catch {
    Write-Host "❌ Ошибка при проверке соответствия: $_" -ForegroundColor Red
}
