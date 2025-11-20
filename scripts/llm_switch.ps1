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

# Log event llm.provider.switched to core.events
$env:PGPASSWORD = "crd12"
$eventSQL = @"
INSERT INTO core.events (source, type, payload)
VALUES ('llm', 'llm.provider.switched', '{"provider": "$Provider", "profile": "$Profile", "timestamp": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')"}'::jsonb);
"@
$eventSQL | Out-File -FilePath "$env:TEMP\llm_switch_event.sql" -Encoding ASCII -Force
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h 127.0.0.1 -p 5433 -U crd_user -d crd12 -f "$env:TEMP\llm_switch_event.sql" | Out-Null
Remove-Item "$env:TEMP\llm_switch_event.sql" -Force
Write-Host "✅ Event logged: llm.provider.switched"
