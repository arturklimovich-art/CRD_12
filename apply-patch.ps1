<#
.SYNOPSIS
    Система применения патчей для CRD12
.DESCRIPTION
    Применяет unified diff патчи к файлам проекта с проверками безопасности
.PARAMETER PatchFile
    Путь к файлу патча
.PARAMETER Container
    Имя Docker контейнера (опционально)
.EXAMPLE
    .\apply-patch.ps1 -PatchFile patches/001-curator-integration-bot.patch -Container crd12_bot
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PatchFile,
    
    [Parameter(Mandatory=$false)]
    [string]$Container = ""
)

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🔧 CRD12 PATCH SYSTEM" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Проверка существования файла патча
if (-not (Test-Path $PatchFile)) {
    Write-Host "❌ ОШИБКА: Файл патча не найден: $PatchFile" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Патч: $PatchFile" -ForegroundColor Yellow
Write-Host ""

# Извлекаем метаданные из патча
$patchContent = Get-Content $PatchFile -Raw
$targetFile = ""
if ($patchContent -match "---\s+a/(.+?)\s") {
    $targetFile = $Matches[1]
}

if (-not $targetFile) {
    Write-Host "❌ ОШИБКА: Не удалось определить целевой файл из патча" -ForegroundColor Red
    exit 1
}

Write-Host "🎯 Целевой файл: $targetFile" -ForegroundColor Cyan
Write-Host ""

# Создаём backup
$backupFile = "$targetFile.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "💾 Создание backup..." -ForegroundColor Yellow
if (Test-Path $targetFile) {
    Copy-Item $targetFile $backupFile
    Write-Host "✅ Backup: $backupFile" -ForegroundColor Green
} else {
    Write-Host "⚠️ Целевой файл не найден, backup не создан" -ForegroundColor Yellow
}
Write-Host ""

# Dry-run проверка
Write-Host "🔍 Проверка патча (dry-run)..." -ForegroundColor Yellow
$dryRunResult = git apply --check $PatchFile 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Патч применим без конфликтов" -ForegroundColor Green
} else {
    Write-Host "❌ ОШИБКА: Патч не может быть применён!" -ForegroundColor Red
    Write-Host "Причина:" -ForegroundColor Yellow
    $dryRunResult | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "💡 Возможные решения:" -ForegroundColor Yellow
    Write-Host "  1. Сбросить файл: git checkout $targetFile" -ForegroundColor White
    Write-Host "  2. Проверить что патч не применён ранее" -ForegroundColor White
    exit 1
}
Write-Host ""

# Применение патча
Write-Host "🚀 Применение патча..." -ForegroundColor Yellow
git apply $PatchFile 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Патч успешно применён к локальному файлу!" -ForegroundColor Green
} else {
    Write-Host "❌ ОШИБКА при применении патча!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Проверка синтаксиса Python (если это .py файл)
if ($targetFile -match "\.py$") {
    Write-Host "🐍 Проверка синтаксиса Python..." -ForegroundColor Yellow
    python -m py_compile $targetFile 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Синтаксис Python корректен" -ForegroundColor Green
    } else {
        Write-Host "❌ ОШИБКА: Синтаксическая ошибка Python!" -ForegroundColor Red
        Write-Host "Откатываем изменения..." -ForegroundColor Yellow
        if (Test-Path $backupFile) {
            Copy-Item $backupFile $targetFile -Force
            Write-Host "✅ Откат выполнен" -ForegroundColor Green
        }
        exit 1
    }
    Write-Host ""
}

# Копирование в контейнер (если указан)
if ($Container) {
    Write-Host "📦 Копирование в контейнер: $Container" -ForegroundColor Yellow
    docker cp $targetFile "${Container}:/$targetFile"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Файл скопирован в контейнер" -ForegroundColor Green
    } else {
        Write-Host "❌ ОШИБКА: Не удалось скопировать в контейнер" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    
    # Проверка синтаксиса в контейнере
    if ($targetFile -match "\.py$") {
        Write-Host "🐍 Проверка синтаксиса в контейнере..." -ForegroundColor Yellow
        docker exec $Container python3 -m py_compile "/$targetFile" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Синтаксис в контейнере корректен" -ForegroundColor Green
        } else {
            Write-Host "❌ ОШИБКА: Синтаксическая ошибка в контейнере!" -ForegroundColor Red
            exit 1
        }
        Write-Host ""
    }
    
    # Перезапуск контейнера
    Write-Host "🔄 Перезапуск контейнера..." -ForegroundColor Yellow
    docker restart $Container | Out-Null
    Write-Host "✅ Контейнер перезапущен" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "⏳ Жду 10 секунд..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    Write-Host ""
    
    # Проверка логов
    Write-Host "📋 Логи контейнера (последние 20 строк):" -ForegroundColor Yellow
    docker logs $Container --tail 20
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ ПАТЧ УСПЕШНО ПРИМЕНЁН!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Статус:" -ForegroundColor Yellow
Write-Host "  ✅ Backup: $backupFile" -ForegroundColor White
Write-Host "  ✅ Патч применён к: $targetFile" -ForegroundColor White
if ($Container) {
    Write-Host "  ✅ Контейнер обновлён: $Container" -ForegroundColor White
}
Write-Host ""
Write-Host "🧪 Следующий шаг: Протестировать функциональность" -ForegroundColor Yellow
Write-Host ""
