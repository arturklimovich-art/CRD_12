# ============================================================================
# agents/EngineersIT.Bot/End-Session.ps1
# АВТОНОМНАЯ система завершения сессии и подготовки контекста для нового чата
# 
# ИСПОЛЬЗОВАНИЕ:
#   .\End-Session.ps1
#   (всё остальное происходит автоматически)
# ============================================================================

param(
    [string]$LastTask = "",
    [string]$SessionSummary = ""
)

$ErrorActionPreference = "Stop"

Write-Host "`n🔄 Завершение сессии и подготовка контекста..." -ForegroundColor Cyan

# АВТООПРЕДЕЛЕНИЕ последней задачи
if (-not $LastTask) {
    $sql = @"
SELECT task_code 
FROM sot.tasks 
WHERE domain_code = 'TL' 
  AND status IN ('completed', 'in_progress')
ORDER BY updated_at DESC NULLS LAST, task_code DESC 
LIMIT 1;
"@
    
    try {
        $LastTask = docker exec -i crd12_pgvector psql -U postgres -d crd12 -t -A -c $sql 2>$null
        $LastTask = $LastTask.Trim()
    } catch {
        $LastTask = "E2-TL-B0-T3"
    }
}

# АВТООПРЕДЕЛЕНИЕ резюме сессии
if (-not $SessionSummary) {
    $sql = @"
SELECT 
    COUNT(DISTINCT b.block_code) as blocks,
    COUNT(DISTINCT t.task_code) as tasks,
    COUNT(s.step_code) as steps,
    STRING_AGG(DISTINCT t.task_code || ': ' || t.title, '; ' ORDER BY t.task_code) FILTER (WHERE t.status = 'completed') as completed
FROM sot.blocks b
LEFT JOIN sot.tasks t ON b.domain_code = t.domain_code AND b.block_code = t.block_code
LEFT JOIN sot.steps s ON t.domain_code = s.domain_code AND t.task_code = s.task_code
WHERE b.domain_code = 'TL';
"@
    
    try {
        $stats = docker exec -i crd12_pgvector psql -U postgres -d crd12 -t -A -F'|' -c $sql 2>$null
        $parts = $stats.Split('|')
        
        $SessionSummary = "✅ Roadmap TL: $($parts[0]) блоков, $($parts[1]) задач, $($parts[2]) шагов. Система моментального контекста работает."
    } catch {
        $SessionSummary = "✅ Работа над проектом CRD_12. Система моментального контекста работает."
    }
}

Write-Host "📊 Последняя задача: $LastTask" -ForegroundColor Yellow
Write-Host "📝 Резюме: $SessionSummary" -ForegroundColor Yellow

# ГЕНЕРАЦИЯ контекста
Write-Host "`n🔧 Генерация контекста..." -ForegroundColor Cyan

& "$PSScriptRoot\Generate-Context-Enhanced.ps1" `
    -LastTask $LastTask `
    -SessionSummary $SessionSummary | Out-Null

# ЗАГРУЗКА в буфер
Write-Host "📋 Загрузка в буфер обмена..." -ForegroundColor Cyan

& "$PSScriptRoot\Load-Context.ps1" | Out-Null

$clipboard = Get-Clipboard
$clipboardLength = $clipboard.Length

if ($clipboardLength -lt 500) {
    Write-Host "❌ ОШИБКА: Контекст слишком короткий!" -ForegroundColor Red
    Write-Host "📄 Проверьте файл: context_for_chat.md" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n✅ ГОТОВО!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📋 В буфере обмена: $clipboardLength символов" -ForegroundColor White
Write-Host "📄 Резервная копия: context_for_chat.md" -ForegroundColor Gray
Write-Host "`n🚀 Открой новый чат → Ctrl+V → Готово!" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan
