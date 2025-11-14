# Main Test Runner for Roadmap Manager Acceptance Tests
param(
    [string[]]$Tests = @("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"),
    [switch]$Quick  # Быстрый тест (только T1-T2)
)

$testsDir = "C:\Users\Artur\Documents\CRD12\tests\roadmap"
. "$testsDir\TestUtils.ps1"

Write-Host "🎯 Roadmap Manager Acceptance Tests" -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Magenta

$results = @()
$startTime = Get-Date

if ($Quick) {
    $Tests = @("T1", "T2")
}

foreach ($test in $Tests) {
    $testScript = "$testsDir\$test-*.ps1"
    if (Test-Path $testScript) {
        $testFile = Get-ChildItem $testScript | Select-Object -First 1
        
        Write-Host "`n🏃 Запуск теста: $test" -ForegroundColor Cyan
        try {
            & $testFile.FullName
            $results += [PSCustomObject]@{
                Test = $test
                Status = "COMPLETED"
                Time = (Get-Date) - $startTime
            }
        } catch {
            $results += [PSCustomObject]@{
                Test = $test
                Status = "FAILED"
                Time = (Get-Date) - $startTime
                Error = $_.Exception.Message
            }
        }
    } else {
        Write-Host "⚠️ Тест $test не найден" -ForegroundColor Yellow
    }
}

# Вывод результатов
Write-Host "`n📊 Результаты тестирования:" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

$completed = ($results | Where-Object { $_.Status -eq "COMPLETED" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAILED" }).Count
$totalTime = (Get-Date) - $startTime

Write-Host "✅ Завершено: $completed" -ForegroundColor Green
Write-Host "❌ Ошибок: $failed" -ForegroundColor Red
Write-Host "⏱️ Общее время: $($totalTime.ToString('mm\:ss'))" -ForegroundColor Cyan

if ($failed -gt 0) {
    Write-Host "`n🔍 Детали ошибок:" -ForegroundColor Red
    $results | Where-Object { $_.Status -eq "FAILED" } | ForEach-Object {
        Write-Host "  $($_.Test): $($_.Error)" -ForegroundColor Red
    }
    exit 1
} else {
    Write-Host "`n🎉 Все тесты пройдены успешно!" -ForegroundColor Green
    exit 0
}
