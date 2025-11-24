# ============================================================================
# agents/EngineersIT.Bot/Load-Context.ps1
# Загрузка и отображение контекста сессии с копированием в буфер обмена
# Автор: arturklimovich-art
# Дата: 2025-11-24
# ============================================================================

param(
    [string]$ContextFile = "context_latest.json"
)

# ============================================================================
# 1. Загрузить JSON контекст
# ============================================================================
$contextPath = Join-Path $PSScriptRoot $ContextFile
if (-not (Test-Path $contextPath)) {
    Write-Host "❌ Файл контекста не найден: $ContextFile" -ForegroundColor Red
    Write-Host "   Запустите Generate-Context-Enhanced.ps1 для создания контекста" -ForegroundColor Yellow
    exit 1
}

try {
    $context = Get-Content $contextPath -Raw | ConvertFrom-Json
} catch {
    Write-Host "❌ Ошибка чтения контекста: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# 2. Вывод в консоль с цветами
# ============================================================================
Write-Host ""
Write-Host "📋 КОНТЕКСТ СЕССИИ" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "👤 Пользователь: " -NoNewline -ForegroundColor White
Write-Host $context.snapshot_metadata.user -ForegroundColor Yellow
Write-Host "📅 Создан: " -NoNewline -ForegroundColor White
Write-Host $context.snapshot_metadata.created_at -ForegroundColor Yellow
if ($context.snapshot_metadata.last_task) {
    Write-Host "🎯 Последняя задача: " -NoNewline -ForegroundColor White
    Write-Host $context.snapshot_metadata.last_task -ForegroundColor Yellow
}
if ($context.snapshot_metadata.session_summary) {
    Write-Host "📝 Резюме: " -NoNewline -ForegroundColor White
    Write-Host $context.snapshot_metadata.session_summary -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🗂️  СТРУКТУРА ПРОЕКТА" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📦 Репозиторий: " -NoNewline -ForegroundColor White
Write-Host $context.project_structure.repo -ForegroundColor Yellow
Write-Host "🌿 Ветка: " -NoNewline -ForegroundColor White
Write-Host $context.project_structure.branch -ForegroundColor Yellow
Write-Host "🐳 Контейнеры: " -NoNewline -ForegroundColor White
Write-Host ($context.project_structure.containers -join ", ") -ForegroundColor Yellow
Write-Host "🗄️  БД: " -NoNewline -ForegroundColor White
Write-Host "$($context.project_structure.database.dbname) @ $($context.project_structure.database.host):$($context.project_structure.database.port)" -ForegroundColor Yellow

Write-Host ""
Write-Host "📊 СОСТОЯНИЕ ROADMAP (домен TL)" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📦 Блоков: " -NoNewline -ForegroundColor White
Write-Host $context.roadmap_state.TL.blocks -ForegroundColor Yellow
Write-Host "📋 Задач: " -NoNewline -ForegroundColor White
Write-Host $context.roadmap_state.TL.tasks -ForegroundColor Yellow
Write-Host "📝 Шагов: " -NoNewline -ForegroundColor White
Write-Host $context.roadmap_state.TL.steps -ForegroundColor Yellow

if ($context.recent_changes -and $context.recent_changes.Count -gt 0) {
    Write-Host ""
    Write-Host "🔄 ПОСЛЕДНИЕ ИЗМЕНЕНИЯ" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    $context.recent_changes | Select-Object -First 5 | ForEach-Object {
        Write-Host "  • " -NoNewline -ForegroundColor White
        Write-Host "[$($_.timestamp)] " -NoNewline -ForegroundColor Gray
        Write-Host "$($_.task_code): " -NoNewline -ForegroundColor Yellow
        Write-Host $_.description -ForegroundColor White
    }
}

if ($context.known_issues -and $context.known_issues.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  ИЗВЕСТНЫЕ ПРОБЛЕМЫ" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    $context.known_issues | ForEach-Object {
        Write-Host "  • " -NoNewline -ForegroundColor White
        Write-Host $_.issue -NoNewline -ForegroundColor Yellow
        Write-Host " [$($_.status)]" -ForegroundColor Gray
        if ($_.workaround) {
            Write-Host "    Workaround: " -NoNewline -ForegroundColor Gray
            Write-Host $_.workaround -ForegroundColor White
        }
    }
}

if ($context.next_steps -and $context.next_steps.Count -gt 0) {
    Write-Host ""
    Write-Host "🎯 СЛЕДУЮЩИЕ ШАГИ" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
    $context.next_steps | ForEach-Object {
        Write-Host "  [$($_.priority)] " -NoNewline -ForegroundColor Gray
        Write-Host "$($_.task): " -NoNewline -ForegroundColor Yellow
        Write-Host "$($_.title) " -NoNewline -ForegroundColor White
        Write-Host "[$($_.status)]" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "🔑 КЛЮЧЕВЫЕ КОМАНДЫ" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  • Синхронизация roadmap: " -NoNewline -ForegroundColor White
Write-Host $context.key_commands.sync_roadmap -ForegroundColor Yellow
Write-Host "  • Информация о домене: " -NoNewline -ForegroundColor White
Write-Host $context.key_commands.get_domain -ForegroundColor Yellow
Write-Host "  • Docker exec: " -NoNewline -ForegroundColor White
Write-Host $context.key_commands.docker_exec -ForegroundColor Yellow
Write-Host "  • Быстрый старт: " -NoNewline -ForegroundColor White
Write-Host $context.key_commands.quick_start -ForegroundColor Yellow

# ============================================================================
# 3. Генерация Markdown для чата
# ============================================================================
$markdown = @"
# 📋 КОНТЕКСТ СЕССИИ

**Пользователь:** $($context.snapshot_metadata.user)  
**Создан:** $($context.snapshot_metadata.created_at)  
**Chat ID:** $($context.snapshot_metadata.chat_id)  
$(if ($context.snapshot_metadata.last_task) { "**Последняя задача:** $($context.snapshot_metadata.last_task)  " })
$(if ($context.snapshot_metadata.session_summary) { "**Резюме:** $($context.snapshot_metadata.session_summary)  " })

---

## 🗂️ СТРУКТУРА ПРОЕКТА

- **Репозиторий:** $($context.project_structure.repo)
- **Ветка:** $($context.project_structure.branch)
- **Домены:** $($context.project_structure.domains -join ", ")
- **Контейнеры:** $($context.project_structure.containers -join ", ")
- **База данных:** $($context.project_structure.database.dbname) @ $($context.project_structure.database.host):$($context.project_structure.database.port)

---

## 📊 СОСТОЯНИЕ ROADMAP (домен TL)

- **Блоков:** $($context.roadmap_state.TL.blocks)
- **Задач:** $($context.roadmap_state.TL.tasks)
- **Шагов:** $($context.roadmap_state.TL.steps)

### Детализация по блокам:

| Блок | Название | Статус | Задач | Шагов |
|------|----------|--------|-------|-------|
"@

# Добавить таблицу блоков
if ($context.roadmap_state.TL.blocks_detail) {
    $context.roadmap_state.TL.blocks_detail | ForEach-Object {
        $markdown += "| $($_.code) | $($_.title) | $($_.status) | $($_.tasks) | $($_.steps) |`n"
    }
}

# Добавить последние изменения
if ($context.recent_changes -and $context.recent_changes.Count -gt 0) {
    $markdown += @"

---

## 🔄 ПОСЛЕДНИЕ ИЗМЕНЕНИЯ

"@
    $context.recent_changes | Select-Object -First 10 | ForEach-Object {
        $markdown += "- **[$($_.timestamp)]** $($_.task_code): $($_.description)`n"
    }
}

# Добавить известные проблемы
if ($context.known_issues -and $context.known_issues.Count -gt 0) {
    $markdown += @"

---

## ⚠️ ИЗВЕСТНЫЕ ПРОБЛЕМЫ

"@
    $context.known_issues | ForEach-Object {
        $markdown += "- **$($_.issue)** [$($_.status)]`n"
        if ($_.workaround) {
            $markdown += "  - Workaround: $($_.workaround)`n"
        }
    }
}

# Добавить следующие шаги
if ($context.next_steps -and $context.next_steps.Count -gt 0) {
    $markdown += @"

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

"@
    $context.next_steps | ForEach-Object {
        $markdown += "$($_.priority). **$($_.task):** $($_.title) [$($_.status)]`n"
    }
}

# Добавить ключевые команды
$markdown += @"

---

## 🔑 КЛЮЧЕВЫЕ КОМАНДЫ

- **Синхронизация roadmap:** ``$($context.key_commands.sync_roadmap)``
- **Информация о домене:** ``$($context.key_commands.get_domain)``
- **Проверка задач:** ``$($context.key_commands.check_tasks)``
- **Docker exec:** ``$($context.key_commands.docker_exec)``
- **Загрузить контекст:** ``$($context.key_commands.load_context)``
- **Быстрый старт:** ``$($context.key_commands.quick_start)``

---

✅ **Контекст восстановлен. Готов к работе!**
"@

# ============================================================================
# 4. Копировать в буфер обмена
# ============================================================================
try {
    if ($IsWindows -or $env:OS -match "Windows") {
        $markdown | Set-Clipboard
        Write-Host ""
        Write-Host "📋 Контекст скопирован в буфер обмена. Вставь его в новый чат (Ctrl+V)." -ForegroundColor Green
    } elseif ($IsLinux) {
        # Linux: используем xclip или xsel
        if (Get-Command xclip -ErrorAction SilentlyContinue) {
            $markdown | xclip -selection clipboard
            Write-Host ""
            Write-Host "📋 Контекст скопирован в буфер обмена (xclip). Вставь его в новый чат (Ctrl+V)." -ForegroundColor Green
        } elseif (Get-Command xsel -ErrorAction SilentlyContinue) {
            $markdown | xsel --clipboard --input
            Write-Host ""
            Write-Host "📋 Контекст скопирован в буфер обмена (xsel). Вставь его в новый чат (Ctrl+V)." -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "⚠️  Буфер обмена недоступен. Markdown сохранён в файл." -ForegroundColor Yellow
            $markdownPath = Join-Path $PSScriptRoot "context_markdown.md"
            $markdown | Out-File -Encoding UTF8 $markdownPath
            Write-Host "📄 Markdown сохранён: $markdownPath" -ForegroundColor Yellow
        }
    } elseif ($IsMacOS) {
        # macOS: используем pbcopy
        $markdown | pbcopy
        Write-Host ""
        Write-Host "📋 Контекст скопирован в буфер обмена. Вставь его в новый чат (Cmd+V)." -ForegroundColor Green
    } else {
        # Fallback: сохранить в файл
        $markdownPath = Join-Path $PSScriptRoot "context_markdown.md"
        $markdown | Out-File -Encoding UTF8 $markdownPath
        Write-Host ""
        Write-Host "📄 Markdown сохранён: $markdownPath" -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "⚠️  Не удалось скопировать в буфер обмена: $_" -ForegroundColor Yellow
    $markdownPath = Join-Path $PSScriptRoot "context_markdown.md"
    $markdown | Out-File -Encoding UTF8 $markdownPath
    Write-Host "📄 Markdown сохранён: $markdownPath" -ForegroundColor Yellow
}

Write-Host "✅ Готов к работе!" -ForegroundColor Green
Write-Host ""
