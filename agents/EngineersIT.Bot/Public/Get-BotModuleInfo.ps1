function Get-BotModuleInfo {
    [CmdletBinding()]
    param()
    
    process {
        $module = Get-Module EngineersIT.Bot
        $functions = Get-Command -Module EngineersIT.Bot
        
        return @{
            ModuleName = $module.Name
            Version = $module.Version
            Functions = $functions.Name
            FunctionsCount = $functions.Count
            Status = "Operational"
        }
    }
}
