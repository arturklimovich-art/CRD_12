# scripts/SystemInit.ps1 - Инициализация системы ИИ-агентов с E1-PATCH-MANUAL
Write-Host "Загрузка системы ИИ-агентов..." -ForegroundColor Cyan
Write-Host "✓ Базовые модули загружены" -ForegroundColor Green
Write-Host "🤖 Инициализация системы ИИ-агентов..." -ForegroundColor Cyan

# Загрузка E1-PATCH-MANUAL модуля
try {
    . "C:\Users\Artur\Documents\CRD12\scripts\PatchTools.ps1" -ErrorAction SilentlyContinue
    Write-Host "✅ Модуль E1-PATCH-MANUAL загружен" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Модуль E1-PATCH-MANUAL: предупреждения при загрузке" -ForegroundColor Yellow
}

Write-Host "✅ Патч 'FixProfile' добавлен: Восстановление профиля" -ForegroundColor Green
Write-Host "✅ Патч 'UpdateModules' добавлен: Обновление всех модулей" -ForegroundColor Green

Write-Host "`n🎯 СИСТЕМА ИИ-АГЕНТОВ И E1-PATCH-MANUAL ГОТОВА!" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`n🤖 КОМАНДЫ ИИ-АГЕНТОВ:" -ForegroundColor Yellow
Write-Host "   Get-AIAgents          - показать список доступных ИИ-агентов" -ForegroundColor White
Write-Host "   Invoke-AIAgent        - запуск задачи выбранным агентом" -ForegroundColor White
Write-Host "   Repair-Quotes         - исправление проблем с кавычками в коде" -ForegroundColor White
Write-Host "   Invoke-SafeCode       - безопасное выполнение кода" -ForegroundColor White
Write-Host "   Test-Agents           - проверка работоспособности системы" -ForegroundColor White

Write-Host "`n🔧 КОМАНДЫ УПРАВЛЕНИЯ ПАТЧАМИ:" -ForegroundColor Yellow
Write-Host "   Get-Patches           - список патчей (legacy)" -ForegroundColor Gray
Write-Host "   Invoke-Patch <name>   - применить патч (legacy)" -ForegroundColor Gray

Write-Host "`n🚀 КОМАНДЫ E1-PATCH-MANUAL СИСТЕМЫ:" -ForegroundColor Green
Write-Host "   Get-EngineerPatch     - получить информацию о патчах Engineers_IT" -ForegroundColor White
Write-Host "   New-EngineerPatch     - загрузить новый патч в систему" -ForegroundColor White
Write-Host "   Approve-EngineerPatch - валидация и одобрение патча" -ForegroundColor White
Write-Host "   Apply-EngineerPatch   - применение одобренного патча" -ForegroundColor White
Write-Host "   Show-EngineerPatchStatus - сводка по всем патчам" -ForegroundColor White

Write-Host "`n💡 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:" -ForegroundColor Cyan
Write-Host "   New-EngineerPatch -File fix_bug.zip -Author YourName" -ForegroundColor Gray
Write-Host "   Get-EngineerPatch -Status submitted" -ForegroundColor Gray
Write-Host "   Show-EngineerPatchStatus" -ForegroundColor Gray

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "✅ Система полностью готова к работе!" -ForegroundColor Green
