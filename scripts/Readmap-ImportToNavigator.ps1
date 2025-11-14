# Readmap-ImportToNavigator.ps1 - УПРОЩЕННАЯ ВЕРСИЯ БЕЗ ЛОГИРОВАНИЯ В БД
param(
    [string]$RoadmapPath = $null,
    [switch]$ForceSnapshot = $false
)

# Настройки
$Script:BasePath = "C:\Users\Artur\Documents\CRD12"
$Script:DbHost = "localhost"
$Script:DbPort = "5433"
$Script:DbUser = "crd_user"
$Script:DbPass = "crd12"
$Script:DbName = "crd12"

# Упрощенная функция логирования (только консоль)
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

# Функция получения активной ревизии
function Get-ActiveRoadmapRevision {
    Write-Log "Получение активной ревизии Roadmap из БД"
    
    $query = "SELECT file_path FROM eng_it.truth_revisions WHERE is_active = true LIMIT 1;"
    $result = psql -h $Script:DbHost -p $Script:DbPort -U $Script:DbUser -d $Script:DbName -t -A -c $query
    
    if ([string]::IsNullOrWhiteSpace($result)) {
        Write-Log "Активная ревизия не найдена в БД" "ERROR"
        return $null
    }
    
    $roadmapPath = $result.Trim()
    Write-Log "Найдена активная ревизия: $roadmapPath"
    
    if (-not (Test-Path $roadmapPath)) {
        Write-Log "Файл Roadmap не найден по пути: $roadmapPath" "WARNING"
        $fileName = [System.IO.Path]::GetFileName($roadmapPath)
        $foundFiles = Get-ChildItem -Path $Script:BasePath -Recurse -Filter $fileName -ErrorAction SilentlyContinue
        if ($foundFiles) {
            $roadmapPath = $foundFiles[0].FullName
            Write-Log "Файл найден по альтернативному пути: $roadmapPath"
        } else {
            Write-Log "Файл Roadmap не найден в проекте" "ERROR"
            return $null
        }
    }
    
    return $roadmapPath
}

# Функция парсинга задач из Roadmap
function Parse-RoadmapTasks {
    param([string]$FilePath)
    
    Write-Log "Парсинг задач из файла: $FilePath"
    
    # Читаем файл с правильной кодировкой
    $content = Get-Content $FilePath -Encoding UTF8 -Raw
    
    $tasks = @()
    $allTaskMatches = [regex]::Matches($content, 'E1-[LB]\d+[^\r\n]*')
    
    Write-Log "Найдено упоминаний задач: $($allTaskMatches.Count)"
    
    foreach ($match in $allTaskMatches) {
        $line = $match.Value
        $taskIdMatch = [regex]::Match($line, '(E1-[LB]\d+)')
        $taskId = $taskIdMatch.Value
        
        if ($taskId -and $tasks.TaskId -notcontains $taskId) {
            $title = $line.Substring($taskIdMatch.Index + $taskIdMatch.Length).Trim()
            $title = $title -replace '^[—\s\-]*', ''
            
            # Определяем статус из Roadmap
            $roadmapStatus = "planned"
            if ($line -match "✅|DONE") {
                $roadmapStatus = "done"
            } elseif ($line -match "🕓|PLANNED") {
                $roadmapStatus = "planned"
            } elseif ($line -match "❌|BLOCKED") {
                $roadmapStatus = "blocked"
            }
            
            # Очищаем заголовок
            $title = $title -replace '[✅🕓❌]', '' -replace '\s+(DONE|PLANNED|BLOCKED).*', ''
            $title = $title.Trim()
            
            # Создаем безопасное название задачи
            $safeTitle = "$taskId $title"
            
            $task = [PSCustomObject]@{
                TaskId = $taskId
                Title = $safeTitle
                RoadmapStatus = $roadmapStatus
                FinalStatus = $roadmapStatus
            }
            $tasks += $task
        }
    }
    
    Write-Log "Успешно обработано задач из Roadmap: $($tasks.Count)"
    return $tasks
}

# Функция проверки верификации задач
function Get-TaskVerification {
    param([array]$Tasks)
    
    Write-Log "Проверка верификации для $($Tasks.Count) задач"
    
    foreach ($task in $Tasks) {
        # Проверяем верифицированный статус в БД
        $verificationQuery = @"
SELECT status, evidence_id 
FROM eng_it.task_verdicts 
WHERE split_part(task_title, ' ', 1) = '$($task.TaskId)'
AND status = 'done'
LIMIT 1;
"@
        $verifiedResult = psql -h $Script:DbHost -p $Script:DbPort -U $Script:DbUser -d $Script:DbName -t -A -c $verificationQuery
        
        if ($verifiedResult) {
            $parts = $verifiedResult -split '\|'
            $verifiedStatus = $parts[0]
            $evidenceId = $parts[1]
            
            # Если задача верифицирована как DONE - приоритет над Roadmap
            if ($verifiedStatus -eq "done") {
                $task.FinalStatus = "done"
                if ($evidenceId) {
                    Write-Log "Задача $($task.TaskId) имеет ВЕРИФИЦИРОВАННЫЙ статус DONE с доказательствами"
                } else {
                    Write-Log "Задача $($task.TaskId) имеет ВЕРИФИЦИРОВАННЫЙ статус DONE без доказательств" "WARNING"
                }
            }
        }
    }
    
    return $Tasks
}

# Функция импорта задач в БД
function Import-TasksToNavigator {
    param([array]$Tasks)
    
    Write-Log "Начало импорта $($Tasks.Count) задач в БД с учетом верификации"
    $imported = 0
    $updated = 0
    $errors = 0
    $statusChanges = 0
    
    foreach ($task in $Tasks) {
        try {
            # Экранируем название задачи для SQL
            $safeTitle = $task.Title -replace "'", "''"
            
            # Проверяем существование задачи по ID задачи (первая часть title)
            $checkQuery = "SELECT id, title, status FROM eng_it.tasks WHERE split_part(title, ' ', 1) = '$($task.TaskId)' LIMIT 1;"
            $existing = psql -h $Script:DbHost -p $Script:DbPort -U $Script:DbUser -d $Script:DbName -t -A -c $checkQuery
            
            $statusChanged = $false
            
            if ($existing -and $existing -ne "") {
                $parts = $existing -split '\|'
                $taskId = $parts[0]
                $existingTitle = $parts[1]
                $currentStatus = $parts[2]
                
                # Обновляем только если статус изменился
                if ($currentStatus -ne $task.FinalStatus) {
                    $updateQuery = "UPDATE eng_it.tasks SET status = '$($task.FinalStatus)', updated_at = NOW() WHERE id = $taskId;"
                    psql -h $Script:DbHost -p $Script:DbPort -U $Script:DbUser -d $Script:DbName -c $updateQuery -q
                    $updated++
                    $statusChanged = $true
                    Write-Log "Обновлена задача: $($task.TaskId) -> $($task.FinalStatus) (было: $currentStatus)"
                } else {
                    Write-Log "Задача $($task.TaskId) уже имеет актуальный статус: $($task.FinalStatus)"
                }
            } else {
                # Вставляем новую задачу
                $insertQuery = "INSERT INTO eng_it.tasks (title, status, created_at, updated_at) VALUES ('$safeTitle', '$($task.FinalStatus)', NOW(), NOW());"
                psql -h $Script:DbHost -p $Script:DbPort -U $Script:DbUser -d $Script:DbName -c $insertQuery -q
                $imported++
                $statusChanged = $true
                Write-Log "Добавлена новая задача: $($task.TaskId) -> $($task.FinalStatus)"
            }
            
            if ($statusChanged) {
                $statusChanges++
            }
            
        } catch {
            $errors++
            Write-Log "Ошибка при обработке задачи $($task.TaskId): $_" "ERROR"
        }
    }
    
    Write-Log "Импорт завершен: добавлено $imported, обновлено $updated, изменений статуса: $statusChanges, ошибок: $errors"
    return @{Imported = $imported; Updated = $updated; StatusChanges = $statusChanges; Errors = $errors}
}

# ОСНОВНОЙ ПРОЦЕСС
Write-Log "=== ЗАПУСК ИМПОРТЕРА ROADMAP → NAVIGATOR С ВЕРИФИКАЦИЕЙ ==="

try {
    # Получаем путь к Roadmap
    if (-not $RoadmapPath) {
        $RoadmapPath = Get-ActiveRoadmapRevision
        if (-not $RoadmapPath) {
            throw "Не удалось определить путь к активной ревизии Roadmap"
        }
    }
    
    # Парсим задачи из Roadmap
    $tasks = Parse-RoadmapTasks -FilePath $RoadmapPath
    if ($tasks.Count -eq 0) {
        throw "Не удалось извлечь задачи из Roadmap"
    }
    
    # Проверяем верификацию и определяем финальный статус
    $tasks = Get-TaskVerification -Tasks $tasks
    
    # Статистика по статусам
    $roadmapDone = ($tasks | Where-Object { $_.RoadmapStatus -eq "done" }).Count
    $finalDone = ($tasks | Where-Object { $_.FinalStatus -eq "done" }).Count
    $verificationOverrides = ($tasks | Where-Object { $_.RoadmapStatus -ne "done" -and $_.FinalStatus -eq "done" }).Count
    
    Write-Log "СТАТИСТИКА СТАТУСОВ:"
    Write-Log "  - В Roadmap как DONE: $roadmapDone"
    Write-Log "  - Финальный статус DONE: $finalDone" 
    Write-Log "  - Переопределено верификацией: $verificationOverrides"
    
    # Импортируем в БД
    $result = Import-TasksToNavigator -Tasks $tasks
    
    # Вызываем создание снапшота при изменениях
    if ($ForceSnapshot -or $result.StatusChanges -gt 0) {
        Write-Log "Запуск автоматического снапшота системы (изменения: $($result.StatusChanges))"
        $snapshotScript = Join-Path $Script:BasePath "scripts\System-Snapshot-Auto.ps1"
        if (Test-Path $snapshotScript) {
            & $snapshotScript -Reason "roadmap_sync"
            Write-Log "Снапшот системы успешно создан"
        } else {
            Write-Log "Скрипт снапшота не найден: $snapshotScript" "WARNING"
        }
    } else {
        Write-Log "Изменений статусов не обнаружено, снапшот не требуется"
    }
    
    Write-Log "=== ИМПОРТЕР УСПЕШНО ЗАВЕРШИЛ РАБОТУ ===" "SUCCESS"
    
} catch {
    Write-Log "КРИТИЧЕСКАЯ ОШИБКА: $_" "ERROR"
    exit 1
}

# ФИНАЛЬНЫЙ ОТЧЕТ
Write-Host "`n=== ФИНАЛЬНЫЙ ОТЧЕТ ИМПОРТА ==="
Write-Host "Обработано задач: $($tasks.Count)"
Write-Host "Добавлено новых: $($result.Imported)"
Write-Host "Обновлено: $($result.Updated)" 
Write-Host "Изменений статуса: $($result.StatusChanges)"
Write-Host "Ошибок: $($result.Errors)"
Write-Host "Верифицированных задач DONE: $finalDone"
Write-Host "===============================`n"

# Показываем итоговые статусы
Write-Host "ИТОГОВЫЕ СТАТУСЫ ЗАДАЧ:"
$tasks | Sort-Object TaskId | ForEach-Object {
    $statusInfo = "$($_.TaskId): $($_.FinalStatus)"
    if ($_.RoadmapStatus -ne $_.FinalStatus) {
        $statusInfo += " (в Roadmap: $($_.RoadmapStatus) → верификация: $($_.FinalStatus))"
    }
    Write-Host "  $statusInfo"
}

Write-Log "Экспорт итоговых статусов завершен"
