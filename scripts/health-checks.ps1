# Health Check Functions for Bot v2 Integration
function Test-EngineerBHealth {
    $engineerBUrl = "http://engineer_b:8060/health"
    try {
        $response = Invoke-RestMethod -Uri $engineerBUrl -Method Get -TimeoutSec 5
        return $response.status -eq "healthy"
    }
    catch {
        Write-Warning "Engineer_B health check failed: $($_.Exception.Message)"
        return $false
    }
}

function Test-JobQueueHealth {
    $jobQueueUrl = "http://job_queue:8050/health" 
    try {
        $response = Invoke-RestMethod -Uri $jobQueueUrl -Method Get -TimeoutSec 5
        return $response.status -eq "healthy"
    }
    catch {
        Write-Warning "Job Queue health check failed: $($_.Exception.Message)"
        return $false
    }
}

function Test-EventsAPIHealth {
    $eventsApiUrl = "http://events_api:8040/health"
    try {
        $response = Invoke-RestMethod -Uri $eventsApiUrl -Method Get -TimeoutSec 5
        return $response.status -eq "healthy"
    }
    catch {
        Write-Warning "Events API health check failed: $($_.Exception.Message)"
        return $false
    }
}

function Get-SystemReadiness {
    $result = @{
        Engineer_B = Test-EngineerBHealth
        JobQueue = Test-JobQueueHealth  
        EventsAPI = Test-EventsAPIHealth
        Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    
    $allHealthy = $result.Engineer_B -and $result.JobQueue -and $result.EventsAPI
    $result["AllSystemsReady"] = $allHealthy
    
    return $result
}
