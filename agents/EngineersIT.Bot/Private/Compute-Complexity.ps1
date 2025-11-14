function Compute-Complexity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text,
        
        [Parameter(Mandatory = $false)]
        [string[]]$Tags = @()
    )
    
    process {
        # Упрощенный расчет сложности для тестирования
        $baseScore = 20
        if ($Text.Length -gt 100) { $baseScore += 20 }
        if ($Tags -contains "security") { $baseScore += 15 }
        if ($Tags -contains "database") { $baseScore += 20 }
        if ($Tags -contains "api") { $baseScore += 10 }
        
        return [Math]::Min($baseScore, 100)
    }
}
