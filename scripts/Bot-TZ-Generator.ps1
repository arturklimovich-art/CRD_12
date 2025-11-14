# СКРИПТ: Bot-TZ-Generator.ps1
# НАЗНАЧЕНИЕ: Автоматическое создание ТЗ из стандартизированного Roadmap
# ВЕРСИЯ: 3.0 - Упрощенный и надежный парсер

param(
    [string]$RoadmapPath = "C:\Users\Artur\Documents\CRD12\ROADMAP\ROADMAP_STANDARD.yaml",
    [string]$Action = "generate"  # generate, validate, status
)

# КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ
$DatabaseConfig = @{
    ContainerName = "crd12_pgvector"
    Database = "crd12"
    Username = "crd_user"
    Password = "crd12"
}

# ФУНКЦИИ СКРИПТА
function Import-StandardizedRoadmap {
    param([string]$Path)
    
    Write-Host "🔍 ЗАГРУЗКА СТАНДАРТИЗИРОВАННОГО ROADMAP..." -ForegroundColor Cyan
    if (-not (Test-Path $Path)) {
        Write-Host "❌ Файл Roadmap не найден: $Path" -ForegroundColor Red
        return $null
    }
    
    try {
        $content = Get-Content $Path -Raw
        Write-Host "✅ Roadmap загружен ($($content.Length) байт)" -ForegroundColor Green
        return Parse-SimpleYaml $content
    }
    catch {
        Write-Host "❌ Ошибка загрузки Roadmap: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Parse-SimpleYaml {
    param([string]$yamlContent)
    
    Write-Host "🔧 ПРОСТОЙ И НАДЕЖНЫЙ ПАРСИНГ YAML..." -ForegroundColor Cyan
    
    $result = @{
        version = ""
        phase = ""
        blocks = @()
    }
    
    # Используем регулярные выражения для простого парсинга
    if ($yamlContent -match 'version:\s*"([^"]+)"') {
        $result.version = $matches[1]
    }
    
    if ($yamlContent -match 'phase:\s*"([^"]+)"') {
        $result.phase = $matches[1]
    }
    
    # Парсим блоки с помощью регулярных выражений
    $blockPattern = '- id:\s*"([^"]+)"\s*alias:\s*"([^"]+)"\s*title:\s*"([^"]+)"\s*status:\s*"([^"]+)"'
    $blockMatches = [regex]::Matches($yamlContent, $blockPattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
    
    Write-Host "📊 Найдено блоков: $($blockMatches.Count)" -ForegroundColor White
    
    foreach ($blockMatch in $blockMatches) {
        $block = @{
            id = $blockMatch.Groups[1].Value
            alias = $blockMatch.Groups[2].Value
            title = $blockMatch.Groups[3].Value
            status = $blockMatch.Groups[4].Value
            tasks = @()
        }
        
        Write-Host "`n📋 БЛОК: $($block.title)" -ForegroundColor Cyan
        Write-Host "   ID: $($block.id)" -ForegroundColor Gray
        Write-Host "   Статус: $($block.status)" -ForegroundColor Gray
        
        # Ищем задачи для этого блока
        $taskPattern = "tasks:\s*((?:\s*-\s*id:\s*`"[^`"]+`".*?)+)"
        $taskSectionMatch = [regex]::Match($yamlContent, $taskPattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)
        
        if ($taskSectionMatch.Success) {
            $taskPattern = '-\s*id:\s*"([^"]+)"\s*title:\s*"([^"]+)"'
            $taskMatches = [regex]::Matches($taskSectionMatch.Value, $taskPattern)
            
            Write-Host "   Задач найдено: $($taskMatches.Count)" -ForegroundColor White
            
            foreach ($taskMatch in $taskMatches) {
                $task = @{
                    id = $taskMatch.Groups[1].Value
                    title = $taskMatch.Groups[2].Value
                    steps = @("Шаг 1: Выполнить задачу", "Шаг 2: Проверить результат")  # Упрощенные шаги
                }
                
                $block.tasks += $task
                Write-Host "     🎯 Задача: $($task.title) ($($task.id))" -ForegroundColor Green
            }
        } else {
            Write-Host "   ❌ Задачи не найдены в блоке" -ForegroundColor Red
        }
        
        $result.blocks += $block
    }
    
    Write-Host "`n✅ Парсинг завершен. Всего блоков: $($result.blocks.Count)" -ForegroundColor Green
    return $result
}

function Generate-TechnicalSpecifications {
    param([hashtable]$roadmapData)
    
    Write-Host "🎯 ГЕНЕРАЦИЯ ТЕХНИЧЕСКИХ ЗАДАНИЙ ИЗ ROADMAP..." -ForegroundColor Magenta
    
    $generatedTZ = @()
    $tzCount = 0
    
    foreach ($block in $roadmapData.blocks) {
        Write-Host "`n📋 ОБРАБОТКА БЛОКА: $($block.title)" -ForegroundColor Cyan
        Write-Host "   Задач в блоке: $($block.tasks.Count)" -ForegroundColor White
        
        foreach ($task in $block.tasks) {
            Write-Host "   🎯 Задача: $($task.title)" -ForegroundColor Yellow
            
            # Создаем ТЗ для каждой задачи
            $tz = @{
                roadmap_task_id = $task.id  # Критическое правило 2
                tz_title = $task.title
                tz_description = "Автоматически сгенерировано из Roadmap. Блок: $($block.title). Статус блока: $($block.status)"
                tz_steps = ($task.steps -join " | ")
                status = if ($block.status -eq "DONE") { "DONE" } else { "PLANNED" }  # Критическое правило 1
                tz_priority = "HIGH"
                created_by = "Bot_Orchestrator_v3"
            }
            
            $generatedTZ += $tz
            $tzCount++
            Write-Host "     ✅ ТЗ создано: $($task.id)" -ForegroundColor Green
        }
    }
    
    Write-Host "`n📊 ИТОГО: Создано $tzCount технических заданий" -ForegroundColor Green
    return $generatedTZ
}

function Save-TZ-To-Database {
    param([array]$technicalSpecifications)
    
    Write-Host "💾 СОХРАНЕНИЕ ТЗ В БАЗУ ДАННЫХ..." -ForegroundColor Cyan
    
    $savedCount = 0
    $errorCount = 0
    
    foreach ($tz in $technicalSpecifications) {
        try {
            # Экранируем кавычки для SQL
            $title = $tz.tz_title -replace "'", "''"
            $description = $tz.tz_description -replace "'", "''"
            $steps = $tz.tz_steps -replace "'", "''"
            
            # Создаем SQL команду для вставки
            $sqlCommand = @"
INSERT INTO eng_it.technical_specifications (
    roadmap_task_id, 
    tz_title, 
    tz_description, 
    tz_steps, 
    status, 
    tz_priority, 
    created_by
) VALUES (
    '$($tz.roadmap_task_id)',
    '$title',
    '$description',
    '$steps',
    '$($tz.status)',
    '$($tz.tz_priority)',
    '$($tz.created_by)'
);
"@
            
            Write-Host "   💾 Сохранение: $($tz.roadmap_task_id)" -ForegroundColor DarkGray
            
            # Выполняем SQL команду
            $output = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$sqlCommand`" 2>&1"
            
            if ($LASTEXITCODE -eq 0 -and $output -notmatch "ERROR") {
                $savedCount++
                Write-Host "   ✅ ТЗ сохранено: $($tz.roadmap_task_id)" -ForegroundColor Green
            } else {
                $errorCount++
                Write-Host "   ❌ Ошибка сохранения: $($tz.roadmap_task_id)" -ForegroundColor Red
                if ($output -and $output.Trim()) {
                    Write-Host "      Ошибка: $output" -ForegroundColor Red
                }
            }
        }
        catch {
            $errorCount++
            Write-Host "   ❌ Исключение: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`n📊 РЕЗУЛЬТАТ СОХРАНЕНИЯ:" -ForegroundColor Cyan
    Write-Host "   ✅ Успешно: $savedCount" -ForegroundColor Green
    Write-Host "   ❌ Ошибки: $errorCount" -ForegroundColor Red
    
    return $savedCount
}

function Get-TZ-Statistics {
    Write-Host "📊 СТАТИСТИКА ТЕХНИЧЕСКИХ ЗАДАНИЙ В БАЗЕ..." -ForegroundColor Cyan
    
    try {
        # Статистика по статусам
        $sqlCommand = "SELECT status, COUNT(*) as count FROM eng_it.technical_specifications GROUP BY status ORDER BY status;"
        $output = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$sqlCommand`""
        Write-Host "📈 СТАТУС ТЗ:" -ForegroundColor Yellow
        if ($output -and $output.Trim()) {
            Write-Host $output -ForegroundColor Gray
        } else {
            Write-Host "   Нет данных" -ForegroundColor Gray
        }
        
        # Общее количество
        $totalCommand = "SELECT COUNT(*) as total_tz FROM eng_it.technical_specifications;"
        $totalOutput = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$totalCommand`""
        Write-Host "📊 ВСЕГО ТЗ:" -ForegroundColor Yellow
        if ($totalOutput -and $totalOutput.Trim()) {
            Write-Host $totalOutput -ForegroundColor Gray
        } else {
            Write-Host "   0" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ Ошибка получения статистики: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ОСНОВНАЯ ЛОГИКА
Write-Host "🎯 BOT ORCHESTRATOR - ГЕНЕРАТОР ТЗ v3.0" -ForegroundColor Magenta
Write-Host "Действие: $Action" -ForegroundColor Cyan

$roadmapData = Import-StandardizedRoadmap -Path $RoadmapPath

if ($roadmapData -and $roadmapData.blocks.Count -gt 0) {
    Write-Host "✅ Roadmap загружен: $($roadmapData.phase)" -ForegroundColor Green
    
    switch ($Action) {
        "generate" {
            $technicalSpecifications = Generate-TechnicalSpecifications -roadmapData $roadmapData
            if ($technicalSpecifications.Count -gt 0) {
                $savedCount = Save-TZ-To-Database -technicalSpecifications $technicalSpecifications
                Write-Host "`n🎉 ГЕНЕРАЦИЯ ТЗ ЗАВЕРШЕНА!" -ForegroundColor Green
                Write-Host "📊 Создано ТЗ: $($technicalSpecifications.Count)" -ForegroundColor Cyan
                Write-Host "📊 Сохранено в БД: $savedCount" -ForegroundColor Cyan
                
                # Показываем статистику после генерации
                Get-TZ-Statistics
            } else {
                Write-Host "❌ Нет задач для генерации ТЗ" -ForegroundColor Red
            }
        }
        "status" {
            Get-TZ-Statistics
        }
        "validate" {
            Write-Host "🔍 ВАЛИДАЦИЯ ROADMAP..." -ForegroundColor Cyan
            Write-Host "Версия: $($roadmapData.version)" -ForegroundColor White
            Write-Host "Фаза: $($roadmapData.phase)" -ForegroundColor White
            Write-Host "Блоков: $($roadmapData.blocks.Count)" -ForegroundColor White
            
            $totalTasks = 0
            foreach ($block in $roadmapData.blocks) {
                $totalTasks += $block.tasks.Count
            }
            Write-Host "Всего задач: $totalTasks" -ForegroundColor Yellow
        }
        default {
            Write-Host "❓ Неизвестное действие: $Action" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ Roadmap не загружен или не содержит блоков" -ForegroundColor Red
}

Write-Host "`n✅ BOT ORCHESTRATOR ВЫПОЛНЕН" -ForegroundColor Green
