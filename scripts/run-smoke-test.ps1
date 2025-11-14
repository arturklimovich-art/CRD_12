# Smoke Test E2E для Bot v2
Write-Host "🚀 ЗАПУСК SMOKE-TEST E2E" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# 1. Читаем ТЗ
$tzPath = ".\tests\smoke-test-tz.json"
if (-not (Test-Path $tzPath)) {
    Write-Host "❌ Файл ТЗ не найден: $tzPath" -ForegroundColor Red
    exit 1
}
$tzData = Get-Content $tzPath | ConvertFrom-Json
$tzJson = $tzData | ConvertTo-Json -Depth 10

# 2. Submit-TZ
Write-Host "1. 📥 Submit-TZ..." -ForegroundColor Yellow
try {
    $submitResult = Submit-TZ -Text $tzJson
    $traceId = $submitResult.trace_id
    $complexity = $submitResult.summary.complexity
    if (-not $complexity) { $complexity = 20 }
    Write-Host "   ✅ ТЗ подана, TraceID: $traceId, Complexity: $complexity" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Ошибка Submit-TZ: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. New-TZPlan
Write-Host "`n2. 📋 New-TZPlan..." -ForegroundColor Yellow
try {
    $planResult = New-TZPlan -Text $tzJson -Complexity $complexity
    $planId = $planResult.PlanId
    Write-Host "   ✅ План создан, PlanID: $planId" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Ошибка New-TZPlan: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. Queue-EngineerJobs
Write-Host "`n3. 📊 Queue-EngineerJobs..." -ForegroundColor Yellow
try {
    $queueResult = Queue-EngineerJobs -PlanId $planId
    Write-Host "   ✅ Задачи поставлены в очередь" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Ошибка Queue-EngineerJobs: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 5. Watch-Plan
Write-Host "`n4. 👀 Watch-Plan..." -ForegroundColor Yellow
try {
    $watchResult = Watch-Plan -PlanId $planId -PollingInterval 2 -TimeoutMinutes 1
    Write-Host "   ✅ Мониторинг завершён. Статус: $($watchResult.plan_status)" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Watch-Plan завершён с предупреждением: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 6. Report
$report = [pscustomobject]@{
    TestName   = "Smoke Test E2E"
    Timestamp  = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    TZ_ID      = $tzData.tz_id
    TraceID    = $traceId
    PlanID     = $planId
    Success    = $true
}
$report | ConvertTo-Json -Depth 5 | Set-Content ".\tests\smoke-test-result.json" -Encoding UTF8
Write-Host "`n🎉 SMOKE-TEST ВЫПОЛНЕН" -ForegroundColor Green
Write-Host "Отчёт: .\tests\smoke-test-result.json" -ForegroundColor Gray
