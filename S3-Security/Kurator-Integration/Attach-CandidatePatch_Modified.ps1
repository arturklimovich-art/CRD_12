# МОДИФИЦИРОВАННАЯ ВЕРСИЯ ATTACH-CANDIDATEPATCH С ИНТЕГРАЦИЕЙ KURATOR
# Добавлена валидация безопасности через Kurator

function Attach-CandidatePatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$JobId,

        [Parameter(Mandatory = $true)]
        [string]$PatchText
    )

    Write-Host "📎 Attaching candidate patch to Job: $JobId" -ForegroundColor Cyan
    
    # 🔐 ШАГ 1: ВАЛИДАЦИЯ БЕЗОПАСНОСТИ ЧЕРЕЗ KURATOR
    Write-Host "🔐 [SECURITY] Запуск проверки безопасности патча..." -ForegroundColor Yellow
    $validationResult = Invoke-KuratorSecurityValidation -PatchContent $PatchText -JobId $JobId
    
    # 🔐 ШАГ 2: ПРОВЕРКА РЕЗУЛЬТАТА ВАЛИДАЦИИ
    if (-not $validationResult.IsSafe) {
        Write-Host "🚫 [SECURITY] Патч отклонен по соображениям безопасности!" -ForegroundColor Red -BackgroundColor White
        Write-Host "   Уровень угрозы: $($validationResult.SecurityLevel)" -ForegroundColor Red
        Write-Host "   Причина: $($validationResult.Issues[0])" -ForegroundColor Yellow
        
        # Запись события о нарушении безопасности
        Write-Host "📝 [EVENT] CANDIDATE_VALIDATION_FAILED: JobId=``" -ForegroundColor Red
        Write-Host "   Security Level: ``" -ForegroundColor Gray
        Write-Host "   Issues: `` detected" -ForegroundColor Gray
        
        # Возврат структуры с информацией об ошибке безопасности
        return @{
            JobId = $JobId
            Message = "Кандидат-патч отклонен по соображениям безопасности"
            Success = $false
            PatchSize = $PatchText.Length
            ValidationStatus = "rejected"
            SecurityLevel = $validationResult.SecurityLevel
            SecurityIssues = $validationResult.Issues
            ValidationResult = $validationResult
        }
    }
    
    Write-Host "✅ [SECURITY] Патч прошел проверку безопасности (Уровень: $($validationResult.SecurityLevel))" -ForegroundColor Green
    
    # 📝 ШАГ 3: СОЗДАНИЕ ЗАДАЧИ (оригинальная логика)
    Write-Host "📝 [EVENT] CANDIDATE_PATCH_ATTACHED: JobId=``" -ForegroundColor Gray
    Write-Host "   Patch size: `` chars" -ForegroundColor Gray

    # Создание задачи для патча (оригинальная логика)
    $patchedTask = @{
        task_id = [guid]::NewGuid().ToString()
        title = "Apply Candidate Patch"
        executor = "Engineer_B"
        payload = @{
            type = "patch"
            content_ref = "inline"
            patch_content = $PatchText
        }
        priority = 2
    }

    # Эмуляция создания задачи в системе
    try {
        # Здесь будет вызов реального API для создания задачи
        # $createdTask = Invoke-JobsUpsert -Tasks @($patchedTask)
        
        Write-Host "✅ Candidate patch attached to new task: ``" -ForegroundColor Green
        
        # 🔐 ШАГ 4: ВОЗВРАТ РАСШИРЕННОЙ СТРУКТУРЫ С ДАННЫМИ БЕЗОПАСНОСТИ
        return @{
            JobId = $JobId
            Message = "Candidate patch attached successfully"
            PatchedTask = $patchedTask
            Success = $true
            PatchSize = $PatchText.Length
            ValidationStatus = "approved"  # 🔐 НОВОЕ ПОЛЕ
            SecurityLevel = $validationResult.SecurityLevel  # 🔐 НОВОЕ ПОЛЕ
            SecurityIssues = $validationResult.Issues  # 🔐 НОВОЕ ПОЛЕ
            ValidatedAt = $validationResult.ValidationTimestamp  # 🔐 НОВОЕ ПОЛЕ
        }
        
    } catch {
        Write-Host "❌ Failed to create task for candidate patch: ``" -ForegroundColor Red
        
        return @{
            JobId = $JobId
            Message = "Failed to attach candidate patch"
            Success = $false
            PatchSize = $PatchText.Length
            ValidationStatus = "error"
            SecurityLevel = $validationResult.SecurityLevel
            Error = $_.Exception.Message
        }
    }
}

# Экспорт модифицированной функции
Export-ModuleMember -Function Attach-CandidatePatch
