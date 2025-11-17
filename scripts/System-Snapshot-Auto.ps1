param(
    [string]$Reason = "status_changed"
)

# 1. Собираем инфо
$systemInfo = [ordered]@{
    timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    docker_containers = @(docker ps --format "{{.Names}} | {{.Status}} | {{.Ports}}")
    project_paths = Get-ChildItem -Path "C:\Users\Artur\Documents\CRD12\" -Directory | Select-Object -ExpandProperty FullName
    roadmap_version = "GENERAL_PLAN_2025-11-05.md"
}

$passportPath = "C:\Users\Artur\Documents\CRD12\workspace\reports\AUDIT_E1_FULL\SYSTEM_PASSPORT.json"
$systemInfo | ConvertTo-Json -Depth 4 | Set-Content $passportPath -Encoding UTF8

# 2. Копируем snapshot в memory/snapshots с timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$snapshotCopyPath = "C:\Users\Artur\Documents\CRD12\memory\snapshots\SYSTEM_PASSPORT_$timestamp.json"
Copy-Item -Path $passportPath -Destination $snapshotCopyPath -Force
Write-Host "✅ Snapshot saved to: $snapshotCopyPath"

# 3. Фиксируем в БД
$env:PGPASSWORD = "crd12"
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h 127.0.0.1 -p 5433 -U crd_user -d crd12 -c "
insert into eng_it.system_snapshots (snapshot_name, description, task_code, database_schema, agent_configs, active_tasks)
values (
  'SYSTEM_PASSPORT_$timestamp',
  'auto snapshot: $Reason',
  'E1-B13',
  '{}'::jsonb,
  '{}'::jsonb,
  jsonb_build_object('files', jsonb_build_array('$snapshotCopyPath', '$passportPath'))
);
" | Out-Null

Write-Host "✅ Snapshot registered in database: SYSTEM_PASSPORT_$timestamp"

# 4. Логируем событие в core.events (только имя файла, без полного пути)
$snapshotFileName = "SYSTEM_PASSPORT_$timestamp.json"
$eventSQL = @"
INSERT INTO core.events (source, type, payload)
VALUES ('system', 'snapshot.done', '{"snapshot_name": "$snapshotFileName", "reason": "$Reason", "location": "memory/snapshots"}'::jsonb);
"@
$eventSQL | Out-File -FilePath "$env:TEMP\snapshot_event.sql" -Encoding ASCII -Force
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h 127.0.0.1 -p 5433 -U crd_user -d crd12 -f "$env:TEMP\snapshot_event.sql" | Out-Null
Remove-Item "$env:TEMP\snapshot_event.sql" -Force

Write-Host "✅ Event logged: snapshot.done"
