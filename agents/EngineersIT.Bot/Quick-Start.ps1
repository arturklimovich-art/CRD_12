# ============================================================================
# agents/EngineersIT.Bot/Quick-Start.ps1
# Единая команда для полного восстановления контекста
# Автор: arturklimovich-art
# Дата: 2025-11-24
# ============================================================================

param(
    [string]$ContextFile = "context_latest.json"
)

Write-Host ""
Write-Host "🚀 БЫСТРЫЙ СТАРТ: Восстановление контекста..." -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan

# ============================================================================
# 1. Загрузить SoT-Commands
# ============================================================================
Write-Host "📦 Загрузка SoT-Commands..." -ForegroundColor White
$sotCommandsPath = Join-Path $PSScriptRoot "SoT-Commands.ps1"

if (Test-Path $sotCommandsPath) {
    try {
        . $sotCommandsPath
        Write-Host "✅ SoT-Commands загружены" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Предупреждение: не удалось загрузить SoT-Commands: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Предупреждение: SoT-Commands.ps1 не найден" -ForegroundColor Yellow
}

# ============================================================================
# 2. Синхронизировать roadmap
# ============================================================================
Write-Host ""
Write-Host "🔄 Синхронизация roadmap..." -ForegroundColor White

if (Get-Command Sync-CoreCatalog -ErrorAction SilentlyContinue) {
    try {
        $syncResult = Sync-CoreCatalog
        if ($syncResult) {
            Write-Host "✅ Roadmap синхронизирован" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Roadmap не синхронизирован (возможно, нет изменений)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Предупреждение: ошибка синхронизации roadmap: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Предупреждение: команда Sync-CoreCatalog недоступна" -ForegroundColor Yellow
}

# ============================================================================
# 3. Загрузить контекст
# ============================================================================
Write-Host ""
Write-Host "📋 Загрузка контекста из файла..." -ForegroundColor White

$loadContextPath = Join-Path $PSScriptRoot "Load-Context.ps1"
if (Test-Path $loadContextPath) {
    try {
        & powershell -File $loadContextPath -ContextFile $ContextFile
    } catch {
        Write-Host "❌ Ошибка загрузки контекста: $_" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Файл Load-Context.ps1 не найден" -ForegroundColor Red
}

# ============================================================================
# 4. Проверить домены
# ============================================================================
Write-Host ""
Write-Host "🗂️  Проверка доменов..." -ForegroundColor White

if (Get-Command Get-Domain -ErrorAction SilentlyContinue) {
    try {
        $domainResult = Get-Domain -DomainCode "TL"
        if ($domainResult) {
            Write-Host "✅ Домен TL проверен" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Предупреждение: не удалось проверить домен TL: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Предупреждение: команда Get-Domain недоступна" -ForegroundColor Yellow
}

# ============================================================================
# 5. Завершение
# ============================================================================
Write-Host ""
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ БЫСТРЫЙ СТАРТ ЗАВЕРШЁН!" -ForegroundColor Green
Write-Host "📋 Контекст скопирован в буфер обмена — вставь его в чат (Ctrl+V)." -ForegroundColor Cyan
Write-Host "🎯 Готов к работе!" -ForegroundColor Green
Write-Host ""
