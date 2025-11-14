# ТЕСТОВЫЙ СКРИПТ ВАЛИДАЦИИ KURATOR
# Цель: Проверка различных типов патчей на соответствие политикам безопасности

Write-Host "🧪 ТЕСТИРОВАНИЕ ВАЛИДАЦИИ КАНДИДАТОВ-ПАТЧЕЙ" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$testCases = @(
    @{
        Name = "БЕЗОПАСНЫЙ ПАТЧ"
        PatchContent = @'
// Safe input validation
function Validate-Input {
    param([string]$input)
    
    if ([string]::IsNullOrWhiteSpace($input)) {
        return $false
    }
    
    $cleanInput = $input.Trim() -replace '[<>{}]', ''
    return $cleanInput.Length -gt 0
}
'@
    },
    @{
        Name = "ОПАСНЫЙ ПАТЧ - УДАЛЕНИЕ ФАЙЛОВ"
        PatchContent = @'
// Dangerous file operations
function Dangerous-Operation {
    param([string]$path)
    
    # This should be rejected by Kurator
    Get-ChildItem C:\ -Recurse | Remove-Item -Force
    return "Files deleted"
}
'@
    },
    @{
        Name = "ПАТЧ С ВНЕШНИМИ ВЫЗОВАМИ"
        PatchContent = @'
// External API calls
function External-Call {
    param([string]$url)
    
    # Potential security risk
    $response = Invoke-RestMethod $url
    return $response
}
'@
    }
)

foreach ($testCase in $testCases) {
    Write-Host "
🧪 ТЕСТ: $($testCase.Name)" -ForegroundColor Yellow
    
    $jobId = [guid]::NewGuid().ToString()
    
    try {
        $result = Attach-CandidatePatch -JobId $jobId -PatchText $testCase.PatchContent
        
        Write-Host "✅ Патч прикреплен" -ForegroundColor Green
        Write-Host "   Candidate ID: $($result.candidate_id)" -ForegroundColor Gray
        Write-Host "   Validation Status: $($result.validation_status)" -ForegroundColor Gray
        
        # Анализ результата валидации
        if ($result.validation_status -eq "approved") {
            Write-Host "   🔒 ВАЛИДАЦИЯ: ОДОБРЕНО" -ForegroundColor Green
        } elseif ($result.validation_status -eq "rejected") {
            Write-Host "   🚫 ВАЛИДАЦИЯ: ОТКЛОНЕНО" -ForegroundColor Red
        } else {
            Write-Host "   ⏳ ВАЛИДАЦИЯ: $($result.validation_status)" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ ОШИБКА: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "
📊 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО" -ForegroundColor Cyan
