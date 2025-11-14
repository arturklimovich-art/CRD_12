# УЛУЧШЕННАЯ ФУНКЦИЯ ВАЛИДАЦИИ KURATOR С ИНТЕГРАЦИЕЙ БЕЗОПАСНОСТИ

function Invoke-KuratorSecurityValidation {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PatchContent,
        
        [Parameter(Mandatory = $true)]
        [string]$JobId,
        
        [string]$PatchType = "code_patch"
    )
    
    Write-Host "🔐 [KURATOR] Запуск валидации безопасности для Job: $JobId" -ForegroundColor Cyan
    Write-Host "   Размер патча: $($PatchContent.Length) символов" -ForegroundColor Gray
    
    # Базовая структура результата валидации
    $validationResult = @{
        IsSafe = $true
        SecurityLevel = "low"  # low, medium, high, critical
        Issues = @()
        Recommendations = @()
        ValidationTimestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        ValidatedBy = "Kurator-Security-Engine"
    }
    
    # СЛОВАРЬ ОПАСНЫХ ПАТТЕРНОВ С УРОВНЯМИ УГРОЗ
    $securityPatterns = @(
        @{Pattern = "Remove-Item.*-Force"; Level = "high"; Description = "Принудительное удаление файлов"},
        @{Pattern = "Stop-Process.*-Force"; Level = "high"; Description = "Принудительная остановка процессов"},
        @{Pattern = "Invoke-Expression|iex"; Level = "critical"; Description = "Динамическое выполнение кода"},
        @{Pattern = "Invoke-WebRequest|Invoke-RestMethod"; Level = "medium"; Description = "Внешние HTTP вызовы"},
        @{Pattern = "System\.Net\.WebClient"; Level = "medium"; Description = "Прямые сетевые операции"},
        @{Pattern = "Get-Item.*HKLM|Set-ItemProperty"; Level = "high"; Description = "Операции с реестром"},
        @{Pattern = "Format-Volume|Restart-Computer"; Level = "critical"; Description = "Критические системные операции"},
        @{Pattern = "Add-LocalGroupMember"; Level = "high"; Description = "Изменение групп пользователей"},
        @{Pattern = "New-LocalUser|Remove-LocalUser"; Level = "high"; Description = "Управление пользователями"},
        @{Pattern = "Disable-WindowsOptionalFeature"; Level = "medium"; Description = "Отключение функций Windows"}
    )
    
    # ПРОВЕРКА БЕЗОПАСНОСТИ
    $threatLevels = @{"low" = 1; "medium" = 2; "high" = 3; "critical" = 4}
    $maxThreatLevel = 1
    
    foreach ($securityPattern in $securityPatterns) {
        if ($PatchContent -match $securityPattern.Pattern) {
            $validationResult.IsSafe = $false
            $currentLevel = $threatLevels[$securityPattern.Level]
            $maxThreatLevel = [Math]::Max($maxThreatLevel, $currentLevel)
            
            $validationResult.Issues += "$($securityPattern.Level.ToUpper()): $($securityPattern.Description)"
            $validationResult.Recommendations += "Заменить опасную операцию на безопасную альтернативу"
        }
    }
    
    # ОПРЕДЕЛЕНИЕ УРОВНЯ БЕЗОПАСНОСТИ
    $validationResult.SecurityLevel = $threatLevels.GetEnumerator() | 
        Where-Object { $_.Value -eq $maxThreatLevel } | 
        Select-Object -First 1 -ExpandProperty Key
    
    # ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ
    if ($PatchContent -match "http://|https://|ftp://") {
        $validationResult.Issues += "MEDIUM: Обнаружены внешние URL вызовы"
        $validationResult.SecurityLevel = "medium"
    }
    
    if ($PatchContent -match "ScriptBlock|\[scriptblock\]") {
        $validationResult.Issues += "HIGH: Обнаружены ScriptBlock операции"
        $validationResult.SecurityLevel = "high"
    }
    
    # ЛОГИРОВАНИЕ РЕЗУЛЬТАТА
    if ($validationResult.IsSafe) {
        Write-Host "✅ [KURATOR] Патч безопасен (Уровень: $($validationResult.SecurityLevel))" -ForegroundColor Green
    } else {
        Write-Host "❌ [KURATOR] Обнаружены проблемы безопасности (Уровень: $($validationResult.SecurityLevel))" -ForegroundColor Red
        Write-Host "   Количество проблем: $($validationResult.Issues.Count)" -ForegroundColor Yellow
        $validationResult.Issues | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    }
    
    return $validationResult
}

function Get-SecurityLevelColor {
    param([string]$SecurityLevel)
    
    switch ($SecurityLevel) {
        "low" { return "Green" }
        "medium" { return "Yellow" } 
        "high" { return "Red" }
        "critical" { return "Red" }
        default { return "White" }
    }
}
