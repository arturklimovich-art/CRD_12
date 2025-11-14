function Watch-Plan {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PlanId,
        
        [Parameter(Mandatory = $false)]
        [int]$PollingInterval = 30,
        
        [Parameter(Mandatory = $false)]
        [int]$TimeoutMinutes = 120,
        
        [Parameter(Mandatory = $false)]
        [switch]$AutoRefine = $true
    )
    
    process {
        try {
            Write-Host "👀 Starting monitoring for Plan: $PlanId" -ForegroundColor Cyan
            Write-Host "⏱️  Polling interval: $($PollingInterval)s, Timeout: $($TimeoutMinutes)m" -ForegroundColor Cyan
            if ($AutoRefine) {
                Write-Host "🔄 Auto-refine: ENABLED" -ForegroundColor Green
            }
                        $startTime = Get-Date
            $timeout = $startTime.AddMinutes($TimeoutMinutes)
            $refinementLog = @()
            $retryCounters = @{}
            
            # Логирование начала мониторинга
            Write-Host "📝 [EVENT] MONITORING_STARTED: PlanId=$PlanId" -ForegroundColor Magenta
            
            do {
                # Временная заглушка - позже заменим на реальный REST запрос
                $planStatus = Get-MockPlanStatus -PlanId $PlanId
                
                Write-Host "📊 Plan Status: $($planStatus.OverallStatus)" -ForegroundColor Yellow
                Write-Host "   Jobs: $($planStatus.CompletedJobs)/$($planStatus.TotalJobs) completed" -ForegroundColor Gray
                
                # Проверка статусов задач
                foreach ($job in $planStatus.Jobs) {
                    Write-Host "   - Job $($job.JobId): $($job.Status)" -ForegroundColor Gray
                    
                    # Реакция на FAILED/STALLED с авто-уточнением
                    if ($job.Status -in @("FAILED", "STALLED") -and $AutoRefine) {
                        Write-Host "🚨 ALERT: Job $($job.JobId) requires refinement!" -ForegroundColor Red
                                                # Автоматический вызов уточнения с кандидат-патчем
                        $refineResult = Refine-Task -JobId $job.JobId -Why $job.ErrorMessage -RetryCount $retryCounters[$job.JobId] -CandidatePatchText $candidatePatch
                        if ($refineResult.Success) {
                            Write-Host "✅ Refinement created $($refineResult.RefinedTasks.Count) new tasks" -ForegroundColor Green
                            $refinementLog += @{
                                JobId = $job.JobId
                                RefinedTasks = $refineResult.RefinedTasks.Count
                                Strategy = $refineResult.Strategy
                            }
                        } else {
                            Write-Host "❌ Refinement failed: $($refineResult.Error)" -ForegroundColor Red
                        }
                    }
                }
                
                # Проверка завершения плана
                if ($planStatus.OverallStatus -in @("COMPLETED", "FAILED")) {
                    Write-Host "🏁 Plan $PlanId finished with status: $($planStatus.OverallStatus)" -ForegroundColor Green
                    break
                }
                
                # Ожидание перед следующим опросом
                if ((Get-Date) -lt $timeout) {
                    Write-Host "⏳ Waiting $PollingInterval seconds..." -ForegroundColor Gray
                    Start-Sleep -Seconds $PollingInterval
                } else {
                    Write-Host "⏰ Monitoring timeout reached" -ForegroundColor Red
                    break
                }
                
            } while ((Get-Date) -lt $timeout)
            
            return @{
                PlanId = $PlanId
                FinalStatus = $planStatus.OverallStatus
                MonitoringDuration = (Get-Date) - $startTime
                JobsProcessed = $planStatus.TotalJobs
                Refinements = $refinementLog
                TotalRefinements = $refinementLog.Count
            }
        }
        catch {
            Write-Error "Monitoring failed: $($_.Exception.Message)"
            return @{
                PlanId = $PlanId
                FinalStatus = "MONITORING_ERROR"
                Error = $_.Exception.Message
            }
        }
    }
}

function Get-MockPlanStatus {
    param([string]$PlanId)
    
    # Генерация случайных статусов для тестирования
    $statuses = @("RUNNING", "PASSED", "FAILED", "STALLED", "CREATED")
    $jobs = @()
    
    for ($i = 1; $i -le 3; $i++) {
        $jobs += @{
            JobId = "$PlanId-job-$i"
            Status = $statuses | Get-Random
            ErrorMessage = if ((Get-Random) -gt 0.7) { "Mock error message" } else { $null }
        }
    }
    
    $completed = ($jobs.Status | Where-Object { $_ -in @("PASSED", "FAILED") }).Count
    $overall = if ($completed -eq $jobs.Count) { "COMPLETED" } else { "RUNNING" }
    
    return @{
        OverallStatus = $overall
        TotalJobs = $jobs.Count
        CompletedJobs = $completed
        Jobs = $jobs
    }
}

