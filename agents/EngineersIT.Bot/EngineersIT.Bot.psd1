@{
    RootModule = 'EngineersIT.Bot.psm1'
    ModuleVersion = '1.0.0'
    GUID = '5a4b21e8-bc23-4677-a691-6336052fb4c4'
    Author = 'EngineersIT Team'
    CompanyName = 'EngineersIT'
    Copyright = '(c) 2025 EngineersIT. All rights reserved.'
    Description = 'AI Orchestrator Bot for EngineersIT - Intelligent task planning and decomposition'
    PowerShellVersion = '5.1'
    
    # ?????????????? ???????
    FunctionsToExport = @('Get-BotModuleInfo', 'Submit-TZ', 'New-TZPlan', 'Queue-EngineerJobs', 'Watch-Plan', 'Refine-Task', 'Attach-CandidatePatch')
    
    # ?????? ??? ???????
    RequiredModules = @()
    
    # ?????????? ??? ????????
    VariablesToExport = '*'
    
    # ?????? ??? ????????  
    AliasesToExport = @()
    
    # ?????, ??????? ???????? ?????? ??????
    FileList = @(
        'EngineersIT.Bot.psm1',
        'EngineersIT.Bot.psd1',
        'Public\Submit-TZ.ps1',
        'Public\New-TZPlan.ps1',
        'Public\Queue-EngineerJobs.ps1', 
        'Public\Watch-Plan.ps1',
        'Public\Refine-Task.ps1',
        'Public\Attach-CandidatePatch.ps1',
        'Public\Get-BotStatus.ps1',
        'Private\Invoke-EventsLog.ps1',
        'Private\Invoke-JobsUpsert.ps1',
        'Private\Compute-Complexity.ps1',
        'Private\Build-Dag.ps1',
        'Private\Select-Playbook.ps1'
    )
}









