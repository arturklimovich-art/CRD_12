param(
  [Parameter(Mandatory=$true)][string]$BackupDir,
  [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin",
  [string]$Host = "localhost",
  [int]$Port = 5433,
  [string]$Db = "crd12",
  [string]$User = "crd_user",
  [string]$Password = "crd12"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $BackupDir)) { throw "BackupDir not found: $BackupDir" }
$eventsCsv = Join-Path $BackupDir 'events.csv'
if (-not (Test-Path $eventsCsv)) { throw "events.csv not found in: $BackupDir" }

$env:PGPASSWORD = $Password
$env:PGCLIENTENCODING = 'UTF8'
$psql = Join-Path $PgBin 'psql.exe'

# 1) Импорт событий во временную таблицу и merge недостающих по id
$sql = @"
BEGIN;
CREATE TEMP TABLE tmp_events (LIKE core.events INCLUDING ALL);
\copy tmp_events FROM '$($eventsCsv -replace '\\','/')' WITH (FORMAT csv, HEADER true)
INSERT INTO core.events (id, ts, source, type, job_id, payload)
SELECT id, ts, source, type, job_id, payload
FROM tmp_events t
WHERE NOT EXISTS (SELECT 1 FROM core.events e WHERE e.id = t.id)
ORDER BY id;
COMMIT;
SELECT 'imported_new_events' AS step, COUNT(*) AS cnt FROM core.events;
SELECT nav.project_roadmap_catchup() AS last_applied_event_id;
"@

$tmpSql = Join-Path $env:TEMP ('restore_events_{0}.sql' -f ([guid]::NewGuid().Guid))
$sql | Set-Content -Encoding UTF8 $tmpSql

& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmpSql
Write-Host "✅ Восстановление завершено. Проекции nav.* обновлены." -ForegroundColor Green
