# AI_System_Interceptor.ps1 - Перехватчик для замены старого интерфейса

# Отключаем старый вывод
$oldOutput = $null

# Загружаем новый единый интерфейс
try {
    . "C:\Users\Artur\Documents\CRD12\scripts\UnifiedSystemInit.ps1"
    
    # Перехватываем и заменяем старые команды
    if (-not (Get-Command Get-Patches -ErrorAction SilentlyContinue)) {
        function global:Get-Patches { 
            Write-Host "ℹ️  Используйте Get-EngineerPatch для новой системы патчей" -ForegroundColor Yellow
            if (Get-Command Get-EngineerPatch -ErrorAction SilentlyContinue) {
                Get-EngineerPatch @args
            } else {
                Write-Host "❌ Модуль E1-PATCH-MANUAL не загружен" -ForegroundColor Red
                Write-Host "   Загрузите: . `$env:CRD12_ROOT\scripts\PatchTools.ps1" -ForegroundColor Yellow
            }
        }
    }
    
    if (-not (Get-Command Invoke-Patch -ErrorAction SilentlyContinue)) {
        function global:Invoke-Patch {
            param([string]$Name)
            Write-Host "ℹ️  Используйте New-EngineerPatch для новой системы патчей" -ForegroundColor Yellow
            Write-Host "Workflow: New-EngineerPatch → Approve-EngineerPatch → Apply-EngineerPatch" -ForegroundColor Cyan
        }
    }
    
} catch {
    Write-Host "⚠️  Ошибка загрузки единого интерфейса: $($_.Exception.Message)" -ForegroundColor Red
}
