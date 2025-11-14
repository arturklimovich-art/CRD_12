function Submit-TZ {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text,
        
        [Parameter(Mandatory = $false)]
        [string[]]$Tags = @()
    )
    
    process {
        try {
            $traceId = [System.Guid]::NewGuid().ToString()
            $planId = [System.Guid]::NewGuid().ToString()
            
            # Логирование начала триажа
            $eventParams = @{
                EventType = "TRIAGE_STARTED"  # ИСПРАВЛЕНО: EventType вместо Type
                TraceId = $traceId
                PlanId = $planId
                Payload = @{
                    text_length = $Text.Length
                    tags = $Tags
                }
            }
            Invoke-EventsLog @eventParams
            
            # Оценка сложности
            $complexityScore = Compute-Complexity -Text $Text -Tags $Tags
            
            # Определение рекомендации по декомпозиции
            if ($complexityScore -le 30) {
                $decompositionRecommendation = "Мелкая задача (выполнить как есть)"
            } elseif ($complexityScore -le 60) {
                $decompositionRecommendation = "Разрезать на 2-4 подзадачи"
            } else {
                $decompositionRecommendation = "Строгая декомпозиция (контракты → каркас → тесты → интеграция → смоук)"
            }
            
            $status = "TRIAGED"
            $summary = "ТЗ принято в обработку. Complexity: $complexityScore. Рекомендация: $decompositionRecommendation"
            
            # Логирование успешного триажа
            $eventParams = @{
                EventType = "TRIAGE_OK"  # ИСПРАВЛЕНО: EventType вместо Type
                TraceId = $traceId
                PlanId = $planId
                Payload = @{
                    summary = $summary
                    tags = $Tags
                    complexity = $complexityScore
                }
            }
            Invoke-EventsLog @eventParams
            
            # Создание результата с правильной структурой
            $result = @{
                TraceId = $traceId
                PlanId = $planId
                Text = $Text  # ДОБАВЛЕНО: исходный текст ТЗ
                ComplexityScore = $complexityScore
                Status = $status
                Tags = $Tags
                Summary = $summary
                DecompositionRecommendation = $decompositionRecommendation
            }
            
            return $result
        }
        catch {
            Write-Error "Triage failed: $($_.Exception.Message)"
            throw
        }
    }
}
