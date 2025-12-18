# ============================================================================
# agents/EngineersIT.Bot/Update-Progress.ps1 (FIXED FINAL)
# Обновление прогресса задач (БЕЗ СЛОЖНОГО JSON)
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$TaskCode,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet('done', 'in_progress', 'planned', 'blocked')]
    [string]$Status,
    
    [string]$Description = "",
    [string]$ChangedBy = "AI_Agent"
)

$ErrorActionPreference = "Stop"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PGCLIENTENCODING = "UTF8"

Write-Host "`n🔄 UPDATE PROGRESS" -ForegroundColor Cyan
Write-Host "Task: $TaskCode → $Status" -ForegroundColor Yellow

$dbHost = "crd12_pgvector"
$dbUser = "crd_user"
$dbName = "crd12"

# Получить ID и старый статус
$getSql = "SELECT id, status FROM eng_it.roadmap_tasks WHERE code = '$TaskCode';"

$current = docker exec -i $dbHost psql -U $dbUser -d $dbName -t -A -F'|' -c $getSql 2>&1

if (-not $current -or -not ($current -match '\|')) {
    Write-Host "`n❌ ERROR: Task '$TaskCode' not found!" -ForegroundColor Red
    exit 1
}

$parts = $current.Split('|')
$taskId = $parts[0].Trim()
$oldStatus = $parts[1].Trim()

Write-Host "Old: $oldStatus → New: $Status" -ForegroundColor Cyan

# Обновить задачу
$descPart = if ($Description) { 
    $cleanDesc = $Description -replace "'", "''"
    ", description = '$cleanDesc'" 
} else { "" }

$updateSql = "UPDATE eng_it.roadmap_tasks SET status = '$Status', updated_at = NOW() $descPart WHERE code = '$TaskCode' RETURNING code, title, status;"

$result = docker exec -i $dbHost psql -U $dbUser -d $dbName -t -A -F'|' -c $updateSql 2>&1

if ($result -match '\|') {
    $resultParts = $result.Split('|')
    Write-Host "`n✅ UPDATED!" -ForegroundColor Green
    Write-Host "   Code: $($resultParts[0].Trim())" -ForegroundColor White
    Write-Host "   Title: $($resultParts[1].Trim())" -ForegroundColor White
    Write-Host "   Status: $($resultParts[2].Trim())" -ForegroundColor Green
    
    # Упрощённое логирование (без сложного JSON парсинга)
    # Используем простой формат без экранирования
    try {
        $eventSql = @"
INSERT INTO eng_it.roadmap_events (entity_type, entity_id, event_type, old_value, new_value, changed_by, ts) 
VALUES ('task', $taskId, 'status_change', '{"status":"$oldStatus"}'::jsonb, '{"status":"$Status"}'::jsonb, '$ChangedBy', NOW());
"@
        
        docker exec -i $dbHost psql -U $dbUser -d $dbName -c $eventSql 2>&1 | Out-Null
        Write-Host "   Event logged ✓" -ForegroundColor Gray
    } catch {
        Write-Host "   Event logging skipped (non-critical)" -ForegroundColor DarkGray
    }
    
} else {
    Write-Host "`n❌ ERROR: Update failed" -ForegroundColor Red
    Write-Host "Result: $result" -ForegroundColor Yellow
}
