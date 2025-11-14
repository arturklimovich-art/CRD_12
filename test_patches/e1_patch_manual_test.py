# Корректный тест E1-PATCH-MANUAL Integration
$EngineerBAPIUrl = "http://localhost:8000"
$ProjectRoot = "C:\Users\Artur\Documents\CRD12"

function Test-E1PatchSystem {
    Write-Host "🎯 ТЕСТ СИСТЕМЫ ПАТЧЕЙ E1-PATCH-MANUAL" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # 1. Проверяем API
    Write-Host "`n1. ПРОВЕРКА API..." -ForegroundColor Yellow
    try {
        $health = Invoke-RestMethod -Uri "$EngineerBAPIUrl/health" -Method Get -TimeoutSec 5
        Write-Host "✅ API доступен: $($health.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ API недоступен: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # 2. Проверяем существующие патчи
    Write-Host "`n2. ПРОВЕРКА СУЩЕСТВУЮЩИХ ПАТЧЕЙ..." -ForegroundColor Yellow
    try {
        $patches = Invoke-RestMethod -Uri "$EngineerBAPIUrl/api/patches" -Method Get -TimeoutSec 5
        $patchCount = if ($patches -is [array]) { $patches.Count } else { if ($patches) { 1 } else { 0 } }
        Write-Host "✅ Найдено патчей: $patchCount" -ForegroundColor Green
        
        if ($patchCount -gt 0) {
            foreach ($patch in $patches) {
                $statusColor = switch ($patch.status) {
                    "submitted" { "Yellow" }
                    "approved" { "Magenta" }
                    "success" { "Green" }
                    default { "White" }
                }
                Write-Host "   - $($patch.status): $($patch.filename) by $($patch.author)" -ForegroundColor $statusColor
            }
        }
    } catch {
        Write-Host "⚠️  Ошибка получения патчей: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 3. Создаем тестовый патч
    Write-Host "`n3. СОЗДАНИЕ ТЕСТОВОГО ПАТЧА..." -ForegroundColor Yellow
    $testDir = "$ProjectRoot\test_patches"
    if (-not (Test-Path $testDir)) { 
        New-Item -ItemType Directory -Path $testDir -Force | Out-Null
    }
    
    # Создаем тестовый файл
    $testFile = "$testDir\e1_final_test_$(Get-Date -Format 'HHmmss').py"
    @'
# E1-PATCH-MANUAL Final Integration Test
def final_integration_test():
    """Финальный тест интеграции E1-PATCH-MANUAL"""
    return "🎉 E1-PATCH-MANUAL Integration - COMPLETE SUCCESS"

if __name__ == "__main__":
    result = final_integration_test()
    print(result)
