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

# Формирование Markdown БЕЗ here-string
$md = "# КОНТЕКСТ СЕССИИ (автоматически восстановлен)`n`n"
$md += "**Дата:** $($context.snapshot_metadata.created_at)`n"
$md += "**Пользователь:** $($context.snapshot_metadata.user)`n"
$md += "**Последняя задача:** **$($context.snapshot_metadata.last_task)**`n"
$md += "**Следующая задача:** **$($context.snapshot_metadata.next_task)**`n`n"
$md += "**Резюме:**`n"
$md += "$($context.snapshot_metadata.session_summary)`n`n"
$md += "---`n`n"

$md += "## СТРУКТУРА ПРОЕКТА`n`n"
$md += "- **Репозиторий:** ``$($context.project_structure.repo)```n"
$md += "- **Ветка:** ``$($context.project_structure.branch)```n"
$md += "- **Домены:** $($context.project_structure.domains -join ', ')`n"
$md += "- **Контейнеры:** $($context.project_structure.containers -join ', ')`n"
$md += "- **БД:** ``$($context.project_structure.database.dbname)`` @ ``$($context.project_structure.database.host):$($context.project_structure.database.port)```n`n"
$md += "---`n`n"

$md += "## ROADMAP ДОМЕНА TL`n`n"
$md += "**Статистика:**`n"
$md += "- Блоков: $($context.roadmap_state.TL.blocks)`n"
$md += "- Задач: $($context.roadmap_state.TL.tasks)`n"
$md += "- Шагов: $($context.roadmap_state.TL.steps)`n`n"

$md += "**Блоки (ТОП-5):**`n`n"
$context.roadmap_state.TL.blocks_detail | Select-Object -First 5 | ForEach-Object {
    $md += "### $($_.code): $($_.title) [$($_.status)]`n"
    $md += "- Задач: $($_.tasks), Шагов: $($_.steps)`n"
    if ($_.completed_tasks) { $md += "- Завершено: $($_.completed_tasks -join ', ')`n" }
    if ($_.in_progress_tasks) { $md += "- В работе: $($_.in_progress_tasks -join ', ')`n" }
    if ($_.planned_tasks) { $md += "- Запланировано: $($_.planned_tasks -join ', ')`n" }
    $md += "`n"
}

$md += "---`n`n"

$md += "## ПОСЛЕДНИЕ ИЗМЕНЕНИЯ (ТОП-6)`n`n"
$context.recent_changes | Select-Object -First 6 | ForEach-Object {
    $md += "- **[$($_.timestamp)]** $($_.description)`n"
}

$md += "`n---`n`n"

$md += "## СЛЕДУЮЩИЕ ШАГИ`n`n"
$context.next_steps | Select-Object -First 5 | ForEach-Object {
    $md += "- **[Приоритет $($_.priority)]** **$($_.task)**: $($_.title) [$($_.status)]`n"
}

$md += "`n---`n`n"

$md += "## КЛЮЧЕВЫЕ КОМАНДЫ`n`n"
$md += "- Синхронизация roadmap: ``$($context.key_commands.sync_roadmap)```n"
$md += "- Информация о домене: ``$($context.key_commands.get_domain)```n"
$md += "- Docker exec: ``$($context.key_commands.docker_exec)```n"
$md += "- Быстрый старт: ``$($context.key_commands.quick_start)```n`n"
$md += "---`n`n"
$md += "**[OK] Контекст восстановлен. Готов к работе!**`n"

# Сохранение в файл (резервная копия)
$md | Out-File -FilePath "context_for_chat.md" -Encoding UTF8

# Копирование в буфер
Set-Clipboard -Value $md

Write-Host "`n[OK] Контекст в буфере ($($md.Length) символов)" -ForegroundColor Green
Write-Host "[INFO] Резервная копия: context_for_chat.md" -ForegroundColor Cyan
