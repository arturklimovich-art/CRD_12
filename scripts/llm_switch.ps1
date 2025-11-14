Param(
  [ValidateSet("local","cloud")] [string]$Provider = "local",
  [ValidateSet("fast","long")] [string]$Profile = "fast",
  [string]$EnvPath = "config/.env"
)
if (!(Test-Path $EnvPath)) { Write-Error "Env file not found: $EnvPath"; exit 1 }
$content = Get-Content $EnvPath -Raw
$content = $content -replace '(?m)^LLM_PROVIDER=.*$', "LLM_PROVIDER=$Provider"
$content = $content -replace '(?m)^LLM_PROFILE=.*$', "LLM_PROFILE=$Profile"
Set-Content -Path $EnvPath -Value $content -Encoding UTF8
Write-Host "Switched LLM to provider=$Provider profile=$Profile"
# TODO: emit event llm.provider.switched to core.events via your CLI
