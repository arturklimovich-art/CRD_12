# ============================================================================
# agents/EngineersIT.Bot/Generate-Context-Enhanced.ps1
# Генерация полного JSON контекста сессии для быстрого восстановления
# Автор: arturklimovich-art
# Дата: 2025-11-24
# ============================================================================

param(
    [string]$OutputFile = "context_latest.json",
    [string]$User = "arturklimovich-art",
    [string]$LastTask = "",
    [string]$SessionSummary = "",
    [string]$DBHost = "localhost",
    [int]$DBPort = 5433,
    [string]$DBName = "crd12",
    [string]$DBUser = "crd_user",
    [string]$DBPassword = "crd12"
)

Write-Host "🔄 Генерация контекста сессии..." -ForegroundColor Cyan

# ============================================================================
# 1. Получить текущую ветку Git
# ============================================================================
try {
    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if (-not $currentBranch) {
        $currentBranch = "unknown"
    }
} catch {
    $currentBranch = "unknown"
}

# ============================================================================
# 2. Генерация chat_id и timestamp
# ============================================================================
$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
$chatId = Get-Date -Format "yyyyMMdd_HHmmss"

# ============================================================================
# 3. SQL запросы для получения данных из БД
# ============================================================================
$env:PGPASSWORD = $DBPassword

# Общая статистика roadmap
$statsQuery = @"
SELECT 
    'blocks' AS entity, COUNT(*) AS total
FROM eng_it.roadmap_blocks WHERE domain_code = 'TL'
UNION ALL
SELECT 'tasks' AS entity, COUNT(*) AS total
FROM eng_it.roadmap_tasks rt
JOIN eng_it.roadmap_blocks rb ON rt.block_id = rb.id
WHERE rb.domain_code = 'TL'
UNION ALL
SELECT 'steps' AS entity, COUNT(*) AS total
FROM eng_it.roadmap_steps rs
JOIN eng_it.roadmap_tasks rt ON rs.task_id = rt.id
JOIN eng_it.roadmap_blocks rb ON rt.block_id = rb.id
WHERE rb.domain_code = 'TL';
"@

$statsResult = $statsQuery | docker exec -i crd12_pgvector psql -h localhost -p $DBPort -U $DBUser -d $DBName -t -A -F'|'

# Парсинг статистики
$blocks = 0
$tasks = 0
$steps = 0
$statsResult -split "`n" | ForEach-Object {
    if ($_ -match "blocks\|(\d+)") { $blocks = [int]$matches[1] }
    if ($_ -match "tasks\|(\d+)") { $tasks = [int]$matches[1] }
    if ($_ -match "steps\|(\d+)") { $steps = [int]$matches[1] }
}

# Детализация по блокам
$blocksQuery = @"
SELECT 
    rb.code, rb.title, rb.status,
    COUNT(DISTINCT rt.id) AS tasks,
    COUNT(rs.id) AS steps,
    STRING_AGG(CASE WHEN rt.status = 'done' THEN rt.code END, '|') AS completed_tasks,
    STRING_AGG(CASE WHEN rt.status = 'in_progress' THEN rt.code END, '|') AS in_progress_tasks,
    STRING_AGG(CASE WHEN rt.status = 'planned' THEN rt.code END, '|') AS planned_tasks
FROM eng_it.roadmap_blocks rb
LEFT JOIN eng_it.roadmap_tasks rt ON rt.block_id = rb.id
LEFT JOIN eng_it.roadmap_steps rs ON rs.task_id = rt.id
WHERE rb.domain_code = 'TL'
GROUP BY rb.code, rb.title, rb.status
ORDER BY rb.code;
"@

$blocksResult = $blocksQuery | docker exec -i crd12_pgvector psql -h localhost -p $DBPort -U $DBUser -d $DBName -t -A -F'|'

# Парсинг блоков
$blocksDetail = @()
$blocksResult -split "`n" | Where-Object { $_ -and $_ -ne "" } | ForEach-Object {
    $parts = $_ -split '\|'
    if ($parts.Length -ge 8) {
        $blocksDetail += @{
            code = $parts[0].Trim()
            title = $parts[1].Trim()
            status = $parts[2].Trim()
            tasks = if ($parts[3]) { [int]$parts[3] } else { 0 }
            steps = if ($parts[4]) { [int]$parts[4] } else { 0 }
            completed_tasks = if ($parts[5]) { $parts[5] -split '\|' | Where-Object { $_ } } else { @() }
            in_progress_tasks = if ($parts[6]) { $parts[6] -split '\|' | Where-Object { $_ } } else { @() }
            planned_tasks = if ($parts[7]) { $parts[7] -split '\|' | Where-Object { $_ } } else { @() }
        }
    }
}

# Последние изменения
$changesQuery = @"
SELECT 
    TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS timestamp,
    'completed_task' AS action,
    code AS task_code,
    title AS description
FROM eng_it.roadmap_tasks rt
JOIN eng_it.roadmap_blocks rb ON rt.block_id = rb.id
WHERE rb.domain_code = 'TL' AND rt.status = 'done'
ORDER BY rt.updated_at DESC LIMIT 10;
"@

$changesResult = $changesQuery | docker exec -i crd12_pgvector psql -h localhost -p $DBPort -U $DBUser -d $DBName -t -A -F'|'

# Парсинг изменений
$recentChanges = @()
$changesResult -split "`n" | Where-Object { $_ -and $_ -ne "" } | ForEach-Object {
    $parts = $_ -split '\|'
    if ($parts.Length -ge 4) {
        $recentChanges += @{
            timestamp = $parts[0].Trim()
            action = $parts[1].Trim()
            task_code = $parts[2].Trim()
            description = $parts[3].Trim()
        }
    }
}

# Следующие задачи
$nextTasksQuery = @"
SELECT rt.code AS task, rt.title, rt.status, rt.priority
FROM eng_it.roadmap_tasks rt
JOIN eng_it.roadmap_blocks rb ON rt.block_id = rb.id
WHERE rb.domain_code = 'TL' AND rt.status = 'planned'
ORDER BY rt.priority ASC, rt.created_at ASC LIMIT 5;
"@

$nextTasksResult = $nextTasksQuery | docker exec -i crd12_pgvector psql -h localhost -p $DBPort -U $DBUser -d $DBName -t -A -F'|'

# Парсинг следующих задач
$nextSteps = @()
$priority = 1
$nextTasksResult -split "`n" | Where-Object { $_ -and $_ -ne "" } | ForEach-Object {
    $parts = $_ -split '\|'
    if ($parts.Length -ge 3) {
        $nextSteps += @{
            priority = $priority++
            task = $parts[0].Trim()
            title = $parts[1].Trim()
            status = $parts[2].Trim()
        }
    }
}

# Определить следующую задачу
$nextTask = if ($nextSteps.Count -gt 0) { $nextSteps[0].task } else { "" }

# ============================================================================
# 4. Загрузить известные проблемы
# ============================================================================
$knownIssuesPath = Join-Path $PSScriptRoot "known_issues.json"
$knownIssues = @()
if (Test-Path $knownIssuesPath) {
    try {
        $knownIssues = Get-Content $knownIssuesPath -Raw | ConvertFrom-Json
    } catch {
        Write-Host "⚠️  Предупреждение: не удалось загрузить known_issues.json" -ForegroundColor Yellow
    }
}

# ============================================================================
# 5. Создать структуру JSON контекста
# ============================================================================
$context = @{
    snapshot_metadata = @{
        created_at = $timestamp
        user = $User
        chat_id = $chatId
        last_task = $LastTask
        next_task = $nextTask
        session_summary = $SessionSummary
    }
    project_structure = @{
        repo = "CRD_12"
        branch = $currentBranch
        domains = @("ENG", "TL")
        containers = @("crd12_engineer_b_api", "crd12_pgvector")
        database = @{
            host = "localhost"
            port = $DBPort
            dbname = $DBName
            user = $DBUser
            schema = "eng_it"
        }
    }
    roadmap_state = @{
        TL = @{
            blocks = $blocks
            tasks = $tasks
            steps = $steps
            blocks_detail = $blocksDetail
        }
    }
    recent_changes = $recentChanges
    known_issues = $knownIssues
    next_steps = $nextSteps
    key_commands = @{
        sync_roadmap = "Sync-CoreCatalog"
        get_domain = "Get-Domain -DomainCode 'TL'"
        check_tasks = "psql -h localhost -p 5433 -U crd_user -d crd12 -c `"SELECT * FROM eng_it.roadmap_tasks WHERE domain_code='TL'`""
        docker_exec = "docker exec -it crd12_engineer_b_api sh"
        load_context = "powershell -File 'agents/EngineersIT.Bot/Load-Context.ps1'"
        quick_start = "powershell -File 'agents/EngineersIT.Bot/Quick-Start.ps1'"
    }
}

# ============================================================================
# 6. Сохранить в файл
# ============================================================================
$outputPath = Join-Path $PSScriptRoot $OutputFile
$context | ConvertTo-Json -Depth 10 | Out-File -Encoding UTF8 $outputPath

# ============================================================================
# 7. Вывод результата
# ============================================================================
Write-Host ""
Write-Host "✅ Контекст сохранён: $OutputFile" -ForegroundColor Green
Write-Host "📊 Статистика:" -ForegroundColor Cyan
Write-Host "   - Блоков: $blocks" -ForegroundColor White
Write-Host "   - Задач: $tasks" -ForegroundColor White
Write-Host "   - Шагов: $steps" -ForegroundColor White
Write-Host "   - Последних изменений: $($recentChanges.Count)" -ForegroundColor White
if ($nextTask) {
    Write-Host "🎯 Следующая задача: $nextTask" -ForegroundColor Yellow
}
if ($SessionSummary) {
    Write-Host "📋 Резюме сессии: $SessionSummary" -ForegroundColor Cyan
}
Write-Host ""
