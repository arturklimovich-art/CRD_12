# ============================================================================
# agents/EngineersIT.Bot/Quick-Start.ps1
# Быстрый старт: одна команда для полного восстановления контекста
# ============================================================================

param(
    [string]$ContextFile = "context_latest.json"
)

Write-Host "`n========================================" -ForegroundColor Gray
Write-Host "БЫСТРЫЙ СТАРТ: Восстановление контекста" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Gray

# 1. Загрузка SoT-Commands
Write-Host "`n[1/4] Загрузка SoT-Commands..." -ForegroundColor Yellow
if (Test-Path "agents\EngineersIT.Bot\SoT-Commands.ps1") {
    . "agents\EngineersIT.Bot\SoT-Commands.ps1"
    Write-Host "[OK] SoT-Commands загружены" -ForegroundColor Green
} else {
    Write-Host "[WARN] SoT-Commands.ps1 не найден, пропускаю..." -ForegroundColor Yellow
}

# 2. Синхронизация roadmap
Write-Host "`n[2/4] Синхронизация roadmap..." -ForegroundColor Yellow
if (Get-Command Sync-CoreCatalog -ErrorAction SilentlyContinue) {
    try {
        Sync-CoreCatalog
        Write-Host "[OK] Roadmap синхронизирован" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Не удалось синхронизировать roadmap: $_" -ForegroundColor Yellow
        Write-Host "[INFO] Продолжаю без синхронизации..." -ForegroundColor Cyan
    }
} else {
    Write-Host "[WARN] Команда Sync-CoreCatalog не найдена, пропускаю..." -ForegroundColor Yellow
}

# 3. Загрузка контекста
Write-Host "`n[3/4] Загрузка контекста из файла..." -ForegroundColor Yellow
$contextPath = Join-Path $PSScriptRoot $ContextFile
if (Test-Path $contextPath) {
    & "$PSScriptRoot\Load-Context.ps1" -ContextFile $ContextFile
} else {
    Write-Host "[WARN] Файл контекста не найден: $contextPath" -ForegroundColor Yellow
    Write-Host "[INFO] Генерирую новый контекст..." -ForegroundColor Cyan
    & "$PSScriptRoot\Generate-Context-Enhanced.ps1" -OutputFile $ContextFile
    & "$PSScriptRoot\Load-Context.ps1" -ContextFile $ContextFile
}

# 4. Проверка доменов
Write-Host "`n[4/4] Проверка доменов..." -ForegroundColor Yellow
if (Get-Command Get-Domain -ErrorAction SilentlyContinue) {
    try {
        $domainResult = Get-Domain -DomainCode "TL"
        if ($domainResult) {
            Write-Host "[OK] Домен TL проверен" -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARN] Не удалось проверить домен: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] Команда Get-Domain не найдена, пропускаю..." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Gray
Write-Host "[OK] БЫСТРЫЙ СТАРТ ЗАВЕРШЁН!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Gray
Write-Host "`n[INFO] Контекст скопирован в буфер обмена - вставь его в чат (Ctrl+V)." -ForegroundColor Cyan
Write-Host "[INFO] Готов к работе!" -ForegroundColor White
Write-Host ""
