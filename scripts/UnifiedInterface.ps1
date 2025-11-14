# UnifiedInterface.ps1 - Единый интерфейс всех систем

function Show-UnifiedSystem {
    # Очищаем экран для чистого отображения
    Clear-Host
    
    Write-Host "🚀 ЗАГРУЗКА ЕДИНОЙ СИСТЕМЫ ENGINEERS_IT" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # Загрузка модулей
    Write-Host "`n📦 ЗАГРУЗКА МОДУЛЕЙ..." -ForegroundColor Yellow
    
    # Проверяем загрузку E1-PATCH-MANUAL
    $E1Loaded = $false
    try {
        . "C:\Users\Artur\Documents\CRD12\scripts\PatchTools.ps1" -ErrorAction SilentlyContinue
        $E1Loaded = (Get-Command Get-EngineerPatch -ErrorAction SilentlyContinue) -ne $null
        if ($E1Loaded) { Write-Host "✅ E1-PATCH-MANUAL система" -ForegroundColor Green }
    } catch {
        Write-Host "⚠️  E1-PATCH-MANUAL: ошибка загрузки" -ForegroundColor Red
    }
    
    Write-Host "✅ Система ИИ-агентов" -ForegroundColor Green
    Write-Host "✅ Базовые инструменты" -ForegroundColor Green
    
    Write-Host "`n🎯 СИСТЕМА ENGINEERS_IT ГОТОВА К РАБОТЕ!" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # ОСНОВНЫЕ КОМАНДЫ - единый стиль
    Write-Host "`n🤖 ОСНОВНЫЕ КОМАНДЫ:" -ForegroundColor Magenta
    Write-Host "   Get-AIAgents          - список ИИ-агентов" -ForegroundColor White
    Write-Host "   Invoke-AIAgent        - запуск задачи агентом" -ForegroundColor White
    Write-Host "   Test-Agents           - проверка системы" -ForegroundColor White
    Write-Host "   Repair-Quotes         - исправление кавычек в коде" -ForegroundColor White
    Write-Host "   Invoke-SafeCode       - безопасное выполнение кода" -ForegroundColor White
    
    # КОМАНДЫ ПАТЧЕЙ - единый стиль
    Write-Host "`n🔧 КОМАНДЫ УПРАВЛЕНИЯ ПАТЧАМИ:" -ForegroundColor Blue
    
    if ($E1Loaded) {
        Write-Host "   Get-EngineerPatch     - информация о патчах" -ForegroundColor White
        Write-Host "   New-EngineerPatch     - загрузить новый патч" -ForegroundColor White
        Write-Host "   Approve-EngineerPatch - валидация и одобрение" -ForegroundColor White
        Write-Host "   Apply-EngineerPatch   - применение патча" -ForegroundColor White
        Write-Host "   Show-EngineerPatchStatus - сводка по патчам" -ForegroundColor White
        
        Write-Host "`n   Get-Patches           - (устаревшее) использовать Get-EngineerPatch" -ForegroundColor Gray
        Write-Host "   Invoke-Patch <name>   - (устаревшее) использовать New-EngineerPatch" -ForegroundColor Gray
    } else {
        Write-Host "   Get-Patches           - список патчей" -ForegroundColor White
        Write-Host "   Invoke-Patch <name>   - применить патч" -ForegroundColor White
        Write-Host "`n   ⚠️  E1-PATCH-MANUAL: для расширенных функций загрузите модуль" -ForegroundColor Yellow
        Write-Host "      . `$env:CRD12_ROOT\scripts\PatchTools.ps1" -ForegroundColor Gray
    }
    
    # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ - единый стиль
    Write-Host "`n💡 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:" -ForegroundColor Green
    
    if ($E1Loaded) {
        Write-Host "   New-EngineerPatch -File fix.zip -Author Name" -ForegroundColor Gray
        Write-Host "   Get-EngineerPatch -Status submitted" -ForegroundColor Gray
        Write-Host "   Show-EngineerPatchStatus" -ForegroundColor Gray
    } else {
        Write-Host "   Get-Patches" -ForegroundColor Gray
        Write-Host "   Invoke-Patch UpdateModules" -ForegroundColor Gray
    }
    
    Write-Host "   Test-Agents" -ForegroundColor Gray
    Write-Host "   Invoke-SafeCode { Get-Process }" -ForegroundColor Gray
    
    Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
    Write-Host "✅ Введите команду для начала работы..." -ForegroundColor Green
}

# Показываем интерфейс сразу
Show-UnifiedSystem
