# EngineersIT.Bot.psm1 - Основной файл модуля
# Автоматическая загрузка всех функций

Write-Host "Loading EngineersIT.Bot module..." -ForegroundColor Green

# Загрузка функций из папки Private
$PrivateDir = "$PSScriptRoot\Private"
if (Test-Path $PrivateDir) {
    $PrivateFunctions = Get-ChildItem -Path "$PrivateDir\*.ps1" -ErrorAction SilentlyContinue
    Write-Host "Loading $($PrivateFunctions.Count) private functions..." -ForegroundColor Gray
    foreach ($Function in $PrivateFunctions) {
        try {
            . $Function.FullName
            Write-Verbose "Loaded private: $($Function.BaseName)"
        } catch {
            Write-Warning "Failed to load private function $($Function.Name): $($_.Exception.Message)"
        }
    }
}

# Загрузка функций из папки Public  
$PublicDir = "$PSScriptRoot\Public"
if (Test-Path $PublicDir) {
    $PublicFunctions = Get-ChildItem -Path "$PublicDir\*.ps1" -ErrorAction SilentlyContinue
    Write-Host "Loading $($PublicFunctions.Count) public functions..." -ForegroundColor Gray
    foreach ($Function in $PublicFunctions) {
        try {
            . $Function.FullName
            Write-Verbose "Loaded public: $($Function.BaseName)"
        } catch {
            Write-Warning "Failed to load public function $($Function.Name): $($_.Exception.Message)"
        }
    }
}

Write-Host "EngineersIT.Bot module loaded successfully!" -ForegroundColor Green
