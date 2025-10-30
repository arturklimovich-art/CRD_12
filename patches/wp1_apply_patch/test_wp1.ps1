# Тестовый скрипт для WP-1
# Проверка работы /agent/apply_patch

Write-Host "🧪 Testing WP-1: /agent/apply_patch" -ForegroundColor Cyan

# Тестовые данные
$testData = @{
    target_filepath = "/app/src/test_wp1.py"
    code = "def test_wp1_function():\\n    return \\\"WP1_TEST_SUCCESS\\\"\\n"
    job_id = "test_wp1_20251029_132317"
} | ConvertTo-Json

try {
    Write-Host "Sending test request..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "http://localhost:8030/api/v1/agent/apply_patch" -Method Post -Body $testData -ContentType "application/json" -TimeoutSec 30
    Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Green
    
    if ($response.status -eq "applied") {
        Write-Host "🎉 WP-1 TEST PASSED! /agent/apply_patch is working!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WP-1 TEST: $($response.message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ WP-1 TEST FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Проверяем события
try {
    Write-Host "
Checking events..." -ForegroundColor Yellow
    $events = Invoke-RestMethod -Uri "http://localhost:8031/events?limit=3" -TimeoutSec 10
    $patchEvents = $events.events | Where-Object { $_.type -like "*PATCH*" }
    
    if ($patchEvents) {
        Write-Host "Recent patch events:" -ForegroundColor Green
        $patchEvents | ForEach-Object { 
            Write-Host "  • $($_.type) - $($_.source) - $($_.ts)" -ForegroundColor White 
        }
    } else {
        Write-Host "No patch events found" -ForegroundColor Gray
    }
} catch {
    Write-Host "Event check failed: $($_.Exception.Message)" -ForegroundColor Red
}
