# Скрипт развертывания ночного цикла в Планировщике заданий

try {
    $TaskName = "CRD12_Nightly_Cycle"
    $ScriptPath = "C:\Users\Artur\Documents\CRD12\scripts\Nightly-Cycle.ps1"
    
    Write-Host "🎯 Настройка задания Планировщика: $TaskName" -ForegroundColor Cyan
    
    # Проверяем существование задания
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Host "⚠️ Задание '$TaskName' уже существует. Удаляем..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ Существующее задание удалено" -ForegroundColor Green
    }
    
    # Создаем действие - запуск PowerShell скрипта
    $action = New-ScheduledTaskAction `
        -Execute "PowerShell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
    
    # Создаем триггер - ежедневно в 2:00 AM
    $trigger = New-ScheduledTaskTrigger `
        -Daily `
        -At "2:00 AM"
    
    # Настройки задания
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -WakeToRun
    
    # Настройки безопасности (запуск с текущими правами)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive `
        -RunLevel Limited
    
    # Регистрируем задание
    $task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Автоматический ночной цикл проверки и отчетности системы CRD12. Запускается ежедневно в 2:00 AM." `
        -Force
    
    Write-Host "✅ Задание Планировщика создано: $TaskName" -ForegroundColor Green
    Write-Host "   🕑 Расписание: Ежедневно в 2:00 AM" -ForegroundColor Gray
    Write-Host "   📝 Скрипт: $ScriptPath" -ForegroundColor Gray
    
    # Включаем задание
    Enable-ScheduledTask -TaskName $TaskName
    Write-Host "✅ Задание активировано" -ForegroundColor Green
    
    # Проверяем созданное задание
    $verifyTask = Get-ScheduledTask -TaskName $TaskName
    Write-Host "`n🔍 Проверка созданного задания:" -ForegroundColor Yellow
    $verifyTask | Format-List TaskName, State, Description
    
    # Создаем файл подтверждения развертывания
    $deploymentInfo = @"
# CRD12 NIGHTLY CYCLE - DEPLOYMENT CONFIRMATION
Развернуто: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Задание: $TaskName
Статус: Активно
Расписание: Ежедневно в 2:00 AM
Скрипт: $ScriptPath

Команда для ручного запуска:
PowerShell -NoProfile -ExecutionPolicy Bypass -File "$ScriptPath"

Команда для проверки статуса:
Get-ScheduledTask -TaskName "$TaskName"
"@
    
    $deploymentInfo | Out-File -FilePath "workspace\reports\NIGHTLY_CYCLE_DEPLOYMENT.md" -Encoding utf8
    Write-Host "✅ Файл подтверждения создан: workspace\reports\NIGHTLY_CYCLE_DEPLOYMENT.md" -ForegroundColor Green
    
}
catch {
    Write-Host "❌ Ошибка при создании задания Планировщика: $_" -ForegroundColor Red
    throw
}
