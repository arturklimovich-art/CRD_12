function Attach-CandidatePatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$JobId,
        
        [Parameter(Mandatory = $true)]
        [string]$PatchText,
        
        [Parameter(Mandatory = $false)]
        [string]$Description,
        
        [Parameter(Mandatory = $false)]
        [string]$Why
    )
    
    process {
        try {
            Write-Host "📎 Attaching candidate patch to Job: $JobId" -ForegroundColor Cyan
            
            if ($Description) {
                Write-Host "📋 Patch description: $Description" -ForegroundColor Gray
            }
            
            if ($Why) {
                Write-Host "🎯 Reason: $Why" -ForegroundColor Gray
            }
            
            # Логирование события прикрепления патча
            Write-Host "📝 [EVENT] CANDIDATE_PATCH_ATTACHED: JobId=$JobId" -ForegroundColor Magenta
            Write-Host "   Patch size: $($PatchText.Length) chars" -ForegroundColor Gray
            
            # Создание задачи с прикрепленным патчем
            $patchedTask = @{
                TaskId = [System.Guid]::NewGuid().ToString()
                Type = "IMPLEMENT"
                Description = "Apply candidate patch: $Description"
                DoD = @("Patch applied successfully", "Tests passing with patch")
                Priority = 85
                Payload = @{
                    original_job_id = $JobId
                    candidate_patch_text = $PatchText
                    patch_description = $Description
                    reason = $Why
                }
            }
            
            Write-Host "✅ Candidate patch attached to new task: $($patchedTask.TaskId)" -ForegroundColor Green
            
            return @{
                Success = $true
                JobId = $JobId
                PatchedTask = $patchedTask
                PatchSize = $PatchText.Length
                Message = "Candidate patch attached successfully"
            }
        }
        catch {
            Write-Error "Failed to attach candidate patch: $($_.Exception.Message)"
            return @{
                Success = $false
                JobId = $JobId
                Error = $_.Exception.Message
            }
        }
    }
}
