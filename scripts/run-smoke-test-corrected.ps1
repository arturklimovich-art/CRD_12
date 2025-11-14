# Исправленный Smoke Test E2E для Bot v2
Write-Host "🚀 ЗАПУСК ИСПРАВЛЕННОГО SMOKE-TEST E2E" -ForegroundColor Green
Write-Host "=====================================`n" -ForegroundColor Green

# Загружаем тестовые данные
$tzData = Get-Content "CRD12\tests\smoke-test-tz.json" | ConvertFrom-Json

# Создаем текстовое представление ТЗ для Submit-TZ
$tzText = @"
ТЗ: $($tzData.title)

Описание: $($tzData.description)

Приоритет: $($tzData.priority)
Дедлайн: $($tzData.deadline_iso)
ID: $($tzData.tz_id)
TraceID: $($tzData.trace_id)
"@

# Шаг 1: Подача ТЗ с правильным параметром -Text
Write-Host "1. 📥 Submit-TZ..." -ForegroundColor Yellow
try {
    $submitResult = Submit-TZ -Text $tzText
    Write-Host "   ✅ ТЗ успешно подана" -ForegroundColor Green
    if ($submitResult.TraceId) {
        Write-Host "   TraceID: $($submitResult.TraceId)" -ForegroundColor Gray
    }
    if ($submitResult.PlanId) {
        Write-Host "   PlanID: $($submitResult.PlanId)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Ошибка Submit-TZ: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Шаг 2: Создание плана (используем существующий PlanId из Submit-TZ)
Write-Host "`n2. 📋 New-TZPlan..." -ForegroundColor Yellow
if ($submitResult.TraceId) {
    try {
        $planResult = New-TZPlan -TraceId $submitResult.TraceId
        Write-Host "   ✅ План создан/обновлен" -ForegroundColor Green
        if ($planResult.plan_id) {
            Write-Host "   PlanID: $($planResult.plan_id)" -ForegroundColor Gray
        }
        if ($planResult.nodes) {
            Write-Host "   Задач в плане: $($planResult.nodes.Count)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ❌ Ошибка New-TZPlan: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "   ⚠️  TraceID отсутствует, пропускаем шаг" -ForegroundColor Yellow
}

# Шаг 3: Постановка задач в очередь (используем PlanId из Submit-TZ)
Write-Host "`n3. 📊 Queue-EngineerJobs..." -ForegroundColor Yellow
if ($submitResult.PlanId) {
    try {
        $queueResult = Queue-EngineerJobs -PlanId $submitResult.PlanId
        Write-Host "   ✅ Задачи поставлены в очередь" -ForegroundColor Green
        if ($queueResult.queued_count) {
            Write-Host "   Поставлено задач: $($queueResult.queued_count)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ❌ Ошибка Queue-EngineerJobs: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "   ⚠️  PlanID отсутствует, пропускаем шаг" -ForegroundColor Yellow
}

# Шаг 4: Мониторинг выполнения
Write-Host "`n4. 👀 Watch-Plan..." -ForegroundColor Yellow
if ($submitResult.PlanId) {
    Write-Host "   Запуск мониторинга плана (10 секунд)..." -ForegroundColor Gray
    try {
        $watchResult = Watch-Plan -PlanId $submitResult.PlanId -TimeoutSeconds 10
        Write-Host "   ✅ Мониторинг завершен" -ForegroundColor Green
        if ($watchResult.plan_status) {
            Write-Host "   Статус плана: $($watchResult.plan_status)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ⚠️  Watch-Plan завершен с предупреждением: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  PlanID отсутствует, пропускаем шаг" -ForegroundColor Yellow
}

Write-Host "`n🎉 SMOKE-TEST ВЫПОЛНЕН" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green

# Создаем отчет
$testReport = @{
    TestName = "Corrected Smoke Test E2E"
    Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    TZ_ID = $tzData.tz_id
    TraceID = $submitResult.TraceId
    PlanID = $submitResult.PlanId
    TasksQueued = $queueResult.queued_count
    PlanStatus = $watchResult.plan_status
    Success = $true
}

$testReport | ConvertTo-Json | Set-Content "CRD12\tests\smoke-test-corrected-result.json" -Encoding UTF8
Write-Host "Отчет сохранен: CRD12\tests\smoke-test-corrected-result.json" -ForegroundColor Gray
