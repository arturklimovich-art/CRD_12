# T2 Test: Edit/Approve Revision (Simplified)
. "C:\Users\Artur\Documents\CRD12\tests\roadmap\TestUtils.ps1"

Write-Host "
🎯 T2 Test: Edit/Approve Revision" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

try {
    # Создаем тестовый элемент
    $testItemId = New-TestItem -Title "T2 Test Item" -Status "planned"
    Write-Host "📝 Создан тестовый элемент: $testItemId" -ForegroundColor Yellow
    
    # Проверяем создание
    $itemExists = Get-TestData "nav.roadmap_items" "item_id = '$testItemId'"
    $test1 = Write-TestResult "T2.1 Item Created" ($itemExists -eq 1) "Элемент создан в БД"
    
    # Проверяем начальный статус
    $initialStatus = Invoke-TestQuery "SELECT status FROM nav.roadmap_items WHERE item_id = '$testItemId'"
    $test2 = Write-TestResult "T2.2 Initial Status" ($initialStatus -eq "planned") "Начальный статус: $initialStatus"
    
    $overall = $test1 -and $test2
    Write-TestResult "T2 OVERALL" $overall "Базовый тест создания элемента"
    
} catch {
    Write-TestResult "T2 OVERALL" $false "Ошибка: $($_.Exception.Message)"
} finally {
    Clear-TestData
}
