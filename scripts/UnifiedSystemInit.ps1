# UnifiedSystemInit.ps1 - Единый интерфейс ИИ-агентов и E1-PATCH-MANUAL

# Загрузка основных модулей
Write-Host "Загрузка системы ИИ-агентов..." -ForegroundColor Cyan
Write-Host "✓ Базовые модули загружены" -ForegroundColor Green

# Загрузка E1-PATCH-MANUAL
try {
    . "C:\Users\Artur\Documents\CRD12\scripts\PatchTools.ps1" -ErrorAction SilentlyContinue
    $E1Loaded = $true
} catch {
    $E1Loaded = $false
}

Write-Host "🤖 Инициализация системы ИИ-агентов..." -ForegroundColor Cyan
Write-Host "✅ Патч 'FixProfile' добавлен: Восстановление профиля" -ForegroundColor Green
Write-Host "✅ Патч 'UpdateModules' добавлен: Обновление всех модулей" -ForegroundColor Green

if ($E1Loaded) {
    Write-Host "✅ Система E1-PATCH-MANUAL загружена" -ForegroundColor Green
}

Write-Host "`n🎯 СИСТЕМА ИИ-АГЕНТОВ И E1-PATCH-MANUAL ГОТОВА!" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Основные команды ИИ-агентов
Write-Host "`n🤖 ОСНОВНЫЕ КОМАНДЫ:" -ForegroundColor Yellow
Write-Host "   Get-AIAgents          - показать список ИИ-агентов" -ForegroundColor White
Write-Host "   Invoke-AIAgent        - запуск задачи агентом" -ForegroundColor White
Write-Host "   Repair-Quotes         - исправление кавычек в коде" -ForegroundColor White
Write-Host "   Invoke-SafeCode       - безопасное выполнение кода" -ForegroundColor White
Write-Host "   Test-Agents           - проверка системы" -ForegroundColor White

# Команды управления патчами
Write-Host "`n🔧 КОМАНДЫ ПАТЧЕЙ:" -ForegroundColor Yellow
Write-Host "   Get-Patches           - список патчей (устаревшее)" -ForegroundColor Gray
Write-Host "   Invoke-Patch <name>   - применить патч (устаревшее)" -ForegroundColor Gray

if ($E1Loaded) {
    Write-Host "`n🚀 E1-PATCH-MANUAL СИСТЕМА:" -ForegroundColor Green
    Write-Host "   Get-EngineerPatch     - информация о патчах Engineers_IT" -ForegroundColor White
    Write-Host "   New-EngineerPatch     - загрузить новый патч" -ForegroundColor White
    Write-Host "   Approve-EngineerPatch - валидация и одобрение" -ForegroundColor White
    Write-Host "   Apply-EngineerPatch   - применение патча" -ForegroundColor White
    Write-Host "   Show-EngineerPatchStatus - сводка по патчам" -ForegroundColor White
    
    Write-Host "`n💡 ПРИМЕРЫ E1-PATCH-MANUAL:" -ForegroundColor Cyan
    Write-Host "   New-EngineerPatch -File fix.zip -Author Name" -ForegroundColor Gray
    Write-Host "   Get-EngineerPatch -Status submitted" -ForegroundColor Gray
    Write-Host "   Show-EngineerPatchStatus" -ForegroundColor Gray
} else {
    Write-Host "`n⚠️  E1-PATCH-MANUAL: модуль не загружен" -ForegroundColor Yellow
    Write-Host "   Загрузите: . `$env:CRD12_ROOT\scripts\PatchTools.ps1" -ForegroundColor Gray
}

Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "✅ Все системы готовы к работе!" -ForegroundColor Green

# Создаем алиасы для обратной совместимости
if ($E1Loaded -and (-not (Get-Command Get-Patches -ErrorAction SilentlyContinue))) {
    function Get-Patches { 
        Write-Host "ℹ️  Используйте Get-EngineerPatch для новой системы" -ForegroundColor Yellow
        Get-EngineerPatch @args
    }
    
    function global:Invoke-Patch {
        param([string]$Name)
        Write-Host "ℹ️  Используйте New-EngineerPatch для новой системы" -ForegroundColor Yellow
        Write-Host "Workflow: New-EngineerPatch → Approve-EngineerPatch → Apply-EngineerPatch" -ForegroundColor Cyan
    }
}
