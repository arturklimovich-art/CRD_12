# T1 Test: Import Roadmap.md → события → проекции
. "C:\Users\Artur\Documents\CRD12\tests\roadmap\TestUtils.ps1"

Write-Host "
🎯 T1 Test: Import Roadmap" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

try {
    # Подготовка тестового файла Roadmap.md
    $testRoadmapContent = @'
# Test Roadmap for Acceptance Testing

## B7-T1 Test Item 1
- **Summary**: Test item for T1 acceptance testing
- **Tech Hints**: powershell, testing
- **Deliverable**: Working test system
- **Priority**: 2
- **Status**: planned
- **Owner**: bot

## B7-T1 Test Item 2  
- **Summary**: Second test item
- **Tech Hints**: postgresql, events
- **Deliverable**: Event system test
- **Priority**: 1
- **Status**: planned
- **Owner**: engineer_b
'@

    $testRoadmapPath = "C:\Users\Artur\Documents\CRD12\config\roadmap\Test_Roadmap.md"
    $testRoadmapContent | Out-File -FilePath $testRoadmapPath -Encoding UTF8
    
    # Запоминаем начальное состояние
    $initialEvents = Get-TestData "core.events"
    $initialItems = Get-TestData "nav.roadmap_items"
    
    # Выполняем импорт
    Write-Host "📥 Выполняем импорт тестового Roadmap..." -ForegroundColor Yellow
    & "C:\Users\Artur\Documents\CRD12\scripts\Roadmap-Import.ps1" -FilePath $testRoadmapPath
    
    # Проверяем результаты
    $finalEvents = Get-TestData "core.events"
    $finalItems = Get-TestData "nav.roadmap_items"
    
    $eventsAdded = $finalEvents - $initialEvents
    $itemsAdded = $finalItems - $initialItems
    
    # Проверки
    $test1 = Write-TestResult "T1.1 Events Created" ($eventsAdded -gt 0) "Создано событий: $eventsAdded"
    $test2 = Write-TestResult "T1.2 Items Created" ($itemsAdded -gt 0) "Создано элементов: $itemsAdded"
    $test3 = Write-TestResult "T1.3 Items in Projections" ((Get-TestData "nav.roadmap_items" "title LIKE '%B7-T1%'") -eq 2) "Найдено тестовых элементов в проекциях"
    
    $overall = $test1 -and $test2 -and $test3
    Write-TestResult "T1 OVERALL" $overall "Тест импорта Roadmap"
    
} catch {
    Write-TestResult "T1 OVERALL" $false "Ошибка: $($_.Exception.Message)"
} finally {
    # Очистка
    if (Test-Path $testRoadmapPath) { Remove-Item $testRoadmapPath }
    Clear-TestData
}
