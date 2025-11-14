function Refine-Task {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$JobId,
        
        [Parameter(Mandatory = $false)]
        [string]$Why,
        
        [Parameter(Mandatory = $false)]
        [int]$RetryCount = 0,
        
        [Parameter(Mandatory = $false)]
        [string]$CandidatePatchText = $null
    )
    
    process {
        try {
            Write-Host "🔄 Starting refinement for Job: $JobId" -ForegroundColor Cyan
            if ($Why) {
                Write-Host "📋 Reason: $Why" -ForegroundColor Gray
            }
            
            # Логирование начала уточнения
            Write-Host "📝 [EVENT] TASK_REFINEMENT: JobId=$JobId, RetryCount=$RetryCount" -ForegroundColor Magenta
            
            # Временная заглушка - получение информации о проваленной задаче
            $failedTask = @{
                JobId = $JobId
                Type = "IMPLEMENT"
                Description = "Mock failed task description for $JobId"
                Error = if ($Why) { $Why } else { "Unknown error" }
            }
            
            Write-Host "📊 Failed task analysis:" -ForegroundColor Yellow
            Write-Host "   - Type: $($failedTask.Type)" -ForegroundColor Gray
            Write-Host "   - Description: $($failedTask.Description)" -ForegroundColor Gray
            Write-Host "   - Error: $($failedTask.Error)" -ForegroundColor Gray
            
            # Проверка необходимости кандидат-патча (после 2+ ретраев)
            $refinedTasks = @()
            if ($RetryCount -ge 2 -and $CandidatePatchText) {
                Write-Host "🎯 Applying candidate patch after $RetryCount retries" -ForegroundColor Yellow
                $patchResult = Attach-CandidatePatch -JobId $JobId -PatchText $CandidatePatchText -Description "Auto-generated patch after $RetryCount failures" -Why $Why
                if ($patchResult.Success) {
                    $refinedTasks = @($patchResult.PatchedTask)
                    Write-Host "✅ Candidate patch applied to refined task" -ForegroundColor Green
                } else {
                    Write-Host "⚠️  Failed to apply candidate patch, using standard refinement" -ForegroundColor Yellow
                    # Стандартная логика уточнения
                    $refinedTasks = Get-StandardRefinementTasks -JobId $JobId -Why $Why
                }
            } else {
                # Стандартная логика уточнения
                $refinedTasks = Get-StandardRefinementTasks -JobId $JobId -Why $Why
            }
            
            # Логирование успешного уточнения
            Write-Host "📝 [EVENT] REFINEMENT_COMPLETED: JobId=$JobId, NewTasks=$($refinedTasks.Count)" -ForegroundColor Magenta
            
            return @{
                Success = $true
                JobId = $JobId
                RefinedTasks = $refinedTasks
                Strategy = if ($CandidatePatchText) { "Patch-based" } else { "Standard" }
                Message = "Created $($refinedTasks.Count) refined tasks"
            }
        }
        catch {
            Write-Error "Refinement failed: $($_.Exception.Message)"
            return @{
                Success = $false
                JobId = $JobId
                Error = $_.Exception.Message
            }
        }
    }
}

# Вспомогательная функция для стандартного уточнения
function Get-StandardRefinementTasks {
    param([string]$JobId, [string]$Why)
    
    $tasks = @(
        @{
            TaskId = [System.Guid]::NewGuid().ToString()
            Type = "ANALYZE"
            Description = "Detailed analysis of failed task: $JobId"
            DoD = @("Root cause identified", "Solution proposed")
            Priority = 90
        },
        @{
            TaskId = [System.Guid]::NewGuid().ToString()
            Type = "IMPLEMENT"
            Description = "Implement fix for: $JobId"
            DoD = @("Fix implemented", "Tests passing")
            Priority = 80
        }
    )
    
    return $tasks
}

