param([string]$ContextFile = "context_latest.json")

Write-Host "`n[LOAD] Загрузка контекста..." -ForegroundColor Cyan

if (-not [System.IO.Path]::IsPathRooted($ContextFile)) {
    $ContextFile = Join-Path $PSScriptRoot $ContextFile
}

if (-not (Test-Path $ContextFile)) {
    Write-Host "[ERROR] Файл контекста не найден: $ContextFile" -ForegroundColor Red
    exit 1
}

$context = Get-Content $ContextFile -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "`n========================================" -ForegroundColor Gray
Write-Host "КОНТЕКСТ СЕССИИ" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Gray
Write-Host "Пользователь: $($context.snapshot_metadata.user)" -ForegroundColor White
Write-Host "Создан: $($context.snapshot_metadata.created_at)" -ForegroundColor White
Write-Host "Последняя задача: $($context.snapshot_metadata.last_task)" -ForegroundColor Yellow
Write-Host "Следующая задача: $($context.snapshot_metadata.next_task)" -ForegroundColor Yellow

Write-Host "`n========================================" -ForegroundColor Gray
Write-Host "ROADMAP (домен TL)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Gray
Write-Host "Блоков: $($context.roadmap_state.TL.blocks)" -ForegroundColor White
Write-Host "Задач: $($context.roadmap_state.TL.tasks)" -ForegroundColor White
Write-Host "Шагов: $($context.roadmap_state.TL.steps)" -ForegroundColor White

if ($context.recent_changes -and $context.recent_changes.Count -gt 0) {
    Write-Host "`n========================================" -ForegroundColor Gray
    Write-Host "ПОСЛЕДНИЕ ИЗМЕНЕНИЯ (ТОП-6)" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Gray
    $context.recent_changes | Select-Object -First 6 | ForEach-Object {
        Write-Host "  [$($_.timestamp)] $($_.description)" -ForegroundColor Cyan
    }
}

if ($context.next_steps -and $context.next_steps.Count -gt 0) {
    Write-Host "`n========================================" -ForegroundColor Gray
    Write-Host "СЛЕДУЮЩИЕ ШАГИ" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Gray
    $context.next_steps | Select-Object -First 5 | ForEach-Object {
        Write-Host "  [$($_.priority)] $($_.task): $($_.title)" -ForegroundColor Cyan
    }
}

$markdown = @"
# КОНТЕКСТ СЕССИИ

**Пользователь:** $($context.snapshot_metadata.user)
**Последняя задача:** $($context.snapshot_metadata.last_task)
**Следующая задача:** $($context.snapshot_metadata.next_task)

## ROADMAP
- Блоков: $($context.roadmap_state.TL.blocks)
- Задач: $($context.roadmap_state.TL.tasks)
- Шагов: $($context.roadmap_state.TL.steps)

**[OK] Готов к работе!**
"@

Set-Clipboard -Value $markdown
Write-Host "`n[OK] Контекст в буфере обмена!" -ForegroundColor Green
