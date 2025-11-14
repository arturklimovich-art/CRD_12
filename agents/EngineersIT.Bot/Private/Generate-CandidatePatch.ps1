function Generate-CandidatePatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$Error,
        
        [Parameter(Mandatory = $false)]
        [string]$JobId,
        
        [Parameter(Mandatory = $false)]
        [string]$Context = "general"
    )
    
    process {
        Write-Host "🤖 Generating candidate patch for job: $JobId" -ForegroundColor Cyan
        
        # Простые шаблоны патчей на основе типа ошибки
        $patchTemplates = @{
            "timeout" = @'
// Fix for timeout issue in job: {0}
public class TimeoutFix {
    public void ExecuteWithTimeout() {
        try {
            // Increased timeout from 30s to 60s
            var result = SomeMethod(TimeSpan.FromSeconds(60));
        } catch (TimeoutException ex) {
            // Log and handle timeout appropriately
            Logger.Warn("Operation timed out: {ex.Message}");
        }
    }
}
'@
            "null_reference" = @'
// Fix for null reference in job: {0}  
public class NullReferenceFix {
    public void SafeMethod(object parameter) {
        if (parameter != null) {
            parameter.DoSomething();
        } else {
            // Handle null case gracefully
            Logger.Info("Parameter was null, skipping operation");
        }
    }
}
'@
            "validation" = @'
// Fix for validation error in job: {0}
public class ValidationFix {
    public bool ValidateInput(string input) {
        if (string.IsNullOrEmpty(input)) {
            return false;
        }
        
        // Additional validation logic
        if (input.Length < 3) {
            return false;
        }
        
        return true;
    }
}
'@
            "general" = @'
// General fix for issue in job: {0}
// Error: {1}
public class GeneralFix {
    public void ApplyFix() {
        try {
            // TODO: Implement specific fix based on error analysis
            // Current issue: {1}
        } catch (Exception ex) {
            // Enhanced error handling
            Logger.Error("Fix application failed: " + ex.Message);
            throw;
        }
    }
}
'@
        }
        
        # Определяем тип ошибки для выбора шаблона
        $patchType = "general"
        if ($Error -match "timeout|timed out") { $patchType = "timeout" }
        elseif ($Error -match "null|null reference") { $patchType = "null_reference" } 
        elseif ($Error -match "valid|validation") { $patchType = "validation" }
        
        # Форматируем патч с параметрами
        $patchText = $patchTemplates[$patchType] -f $JobId, $Error
        
        Write-Host "   Generated $patchType patch ($($patchText.Length) chars)" -ForegroundColor Gray
        return $patchText
    }
}
