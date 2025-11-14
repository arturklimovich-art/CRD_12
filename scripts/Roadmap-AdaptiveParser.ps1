# Adapted Roadmap Parser - Адаптированный парсер Roadmap
param(
    [string]$OutputPath = "workspace\reports\ROADMAP_ADAPTED_REPORT.md",
    [switch]$OpenAfterGenerate
)

try {
    Write-Host "🎯 АДАПТИРОВАННЫЙ АНАЛИЗ ROADMAP..." -ForegroundColor Cyan
    
    $roadmapPath = "workspace\readmap\revisions\GENERAL_PLAN_2025-11-05.md"
    
    if (-not (Test-Path $roadmapPath)) {
        Write-Host "❌ Roadmap файл не найден" -ForegroundColor Red
        return
    }
    
    $content = Get-Content $roadmapPath
    Write-Host "✅ Анализируем Roadmap: $($content.Count) строк" -ForegroundColor Green
    
    # Адаптивный парсинг - берем ВСЕ значимые строки как задачи
    $allTasks = @()
    $currentSection = "Общие"
    
    foreach ($line in $content) {
        $trimmed = $line.Trim()
        
        # Определяем секции
        if ($trimmed -match "^#+\s+(.+)") {
            $currentSection = $matches[1]
            continue
        }
        
        # Берем любые непустые строки как потенциальные задачи
        if ($trimmed -ne "" -and 
            $trimmed -notmatch "^---" -and 
            $trimmed -notmatch "^\`\`\`" -and
            $trimmed -notmatch "^\|" -and
            $trimmed.Length -gt 10) {  # Исключаем очень короткие строки
            
            # Определяем статус если есть маркеры
            $status = " "
            $description = $trimmed
            
            if ($trimmed -match "^\s*[-*•]\s*\[(.)\]\s*(.+)") {
                $status = $matches[1]
                $description = $matches[2]
            }
            elseif ($trimmed -match "^\s*[-*•]\s*(.+)") {
                $description = $matches[1]
            }
            elseif ($trimmed -match "^\s*\d+\.\s*(.+)") {
                $description = $matches[1]
            }
            
            $allTasks += @{
                Section = $currentSection
                Status = $status
                Description = $description
                OriginalLine = $trimmed
                SystemStatus = "🔍 Требует анализа"
                Evidence = "Не синхронизировано с Navigator"
            }
        }
    }
    
    Write-Host "✅ Выявлено потенциальных задач: $($allTasks.Count)" -ForegroundColor Green
    
    # Генерация отчета
    $report = @"
# АДАПТИВНЫЙ ОТЧЕТ О СООТВЕТСТВИИ ROADMAP
> Сгенерировано: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> 
> **Метод:** Адаптивный анализ всего содержимого Roadmap
> **Статус:** Диагностика структуры источника истины

## 📊 РЕЗУЛЬТАТЫ АНАЛИЗА

### 🔍 ДИАГНОСТИКА СТРУКТУРЫ
- **Проанализировано строк:** $($content.Count)
- **Выявлено задач:** $($allTasks.Count)
- **Секций:** $(($allTasks.Section | Sort-Object -Unique).Count)

### 🎯 ВЫЯВЛЕННЫЕ ЗАДАЧИ И СЕКЦИИ
$(if ($allTasks.Count -eq 0) {
"**❌ НЕ УДАЛОСЬ ВЫЯВИТЬ ЗАДАЧИ**`n`nРекомендации:`n1. Проверьте формат Roadmap файла`n2. Убедитесь что файл содержит задачи развития системы`n3. Рассмотрите стандартизацию формата`n`n"
} else {
    $reportSections = ""
    $sections = $allTasks.Section | Sort-Object -Unique
    
    foreach ($section in $sections) {
        $sectionTasks = $allTasks | Where-Object { $_.Section -eq $section }
        $reportSections += "### 📁 $section`n`n"
        $reportSections += "| Статус | Задача | Статус в системе |`n|--------|--------|------------------|`n"
        
        foreach ($task in $sectionTasks) {
            $statusIcon = switch ($task.Status) {
                "x" { "✅" }
                " " { "📝" }
                default { "📝" }
            }
            $reportSections += "| $statusIcon | $($task.Description) | $($task.SystemStatus) |`n"
        }
        $reportSections += "`n"
    }
    
    $reportSections
})

## 🎯 СИСТЕМНАЯ АРХИТЕКТУРА

### 🔄 ТЕКУЩИЙ WORKFLOW
1. **Roadmap** - источник истины *(требует анализа формата)*
2. **Bot Orchestrator** - создает ТЗ *(готов)*
3. **Navigator** - управление задачами *(готов)*
4. **Engineer_B-API** - выполнение задач *(готов)*
5. **DoV-Runner** - верификация *(работает)*
6. **Curator** - интеграция *(работает)*

## 🚀 РЕКОМЕНДАЦИИ

### 🔧 НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ
1. **Стандартизировать формат Roadmap** для автоматического парсинга
2. **Определить критерии задач** в источнике истины
3. **Настроить импортёр** под фактический формат

### 📈 ДОЛГОСРОЧНЫЕ ЦЕЛИ
- Автоматическое создание ТЗ из стандартизированного Roadmap
- Полная синхронизация всех компонентов системы
- Самопроверяющаяся и самосинхронизирующаяся архитектура

---
*Для работы системы необходим стандартизированный формат Roadmap*
*Отчет сгенерирован адаптивным анализатором*
"@

    # Сохранение отчета
    $OutputDir = Split-Path $OutputPath -Parent
    if (!(Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force
    }
    
    $report | Out-File -FilePath $OutputPath -Encoding utf8

    Write-Host "✅ Адаптированный отчет создан: $OutputPath" -ForegroundColor Green

    if ($OpenAfterGenerate) {
        Invoke-Item $OutputPath
    }
}
catch {
    Write-Host "❌ Ошибка при адаптивном анализе: $_" -ForegroundColor Red
}
