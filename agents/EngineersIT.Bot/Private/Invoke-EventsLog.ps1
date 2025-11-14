function Invoke-EventsLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$EventType,
        
        [Parameter(Mandatory = $true)]
        [string]$TraceId,
        
        [Parameter(Mandatory = $false)]
        [string]$PlanId,
        
        [Parameter(Mandatory = $false)]
        [string]$JobId,
        
        [Parameter(Mandatory = $false)]
        [string]$ParentTaskId,
        
        [Parameter(Mandatory = $false)]
        [hashtable]$Payload,
        
        [Parameter(Mandatory = $false)]
        [string]$Severity = "info"
    )
    
    begin {
        Write-Verbose "Preparing to log event: $EventType"
    }
    
    process {
        try {
            # Формирование события согласно контракту §7.1
            $eventData = @{
                event_id = [System.Guid]::NewGuid().ToString()
                ts = [System.DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
                source = "bot_orchestrator"
                type = $EventType
                trace_id = $TraceId
                job_id = $JobId
                plan_id = $PlanId
                parent_task_id = $ParentTaskId
                payload = $Payload
                severity = $Severity
                version = "v1"
            }
            
            # TODO: Реализовать фактическую отправку через REST API
            # $response = Invoke-RestMethod -Uri "$Script:EventsAPIBaseUrl/events/log" -Method Post -Body ($eventData | ConvertTo-Json -Depth 10) -ContentType "application/json"
            
            # Временная заглушка - вывод в консоль
            Write-Host "EVENT_LOGGED: $EventType" -ForegroundColor Green
            Write-Host "  TraceId: $TraceId" -ForegroundColor Gray
            Write-Host "  PlanId: $PlanId" -ForegroundColor Gray
            if ($Payload) {
                Write-Host "  Payload: $($Payload | ConvertTo-Json -Compress)" -ForegroundColor Gray
            }
            
            # Возвращаем данные события для отладки
            return $eventData
            
        } catch {
            Write-Warning "Не удалось залогировать событие $EventType : $($_.Exception.Message)"
            # Возвращаем пустой результат при ошибке
            return $null
        }
    }
    
    end {
        Write-Verbose "Event logging completed for: $EventType"
    }
}
