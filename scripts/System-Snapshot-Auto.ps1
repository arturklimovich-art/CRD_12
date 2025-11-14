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

# 2. Фиксируем в БД
$env:PGPASSWORD = "crd12"
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -h 127.0.0.1 -p 5433 -U crd_user -d crd12 -c "
insert into eng_it.system_snapshots (snapshot_name, description, task_code, database_schema, agent_configs, active_tasks)
values (
  'SYSTEM_PASSPORT_' || to_char(now(),'YYYYMMDD_HH24MISS'),
  'auto snapshot: $Reason',
  'E1-B13',
  '{}'::jsonb,
  '{}'::jsonb,
  jsonb_build_object('files', jsonb_build_array('$passportPath'))
);
" | Out-Null
