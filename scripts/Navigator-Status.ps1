param(
  [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin",
  [string]$Host = "localhost",
  [int]$Port = 5433,
  [string]$Db = "crd12",
  [string]$User = "crd_user",
  [string]$Password = "crd12",
  [int]$Top = 50
)
$ErrorActionPreference="Stop"
$env:PGPASSWORD=$Password
$env:PGCLIENTENCODING='UTF8'
$psql = Join-Path $PgBin 'psql.exe'
$tmp = Join-Path $env:TEMP ('navigator_status_{0}.sql' -f ([guid]::NewGuid().Guid))
@"
SELECT * FROM nav.navigator_plan;
SELECT item_id, title, status, priority, owner, order_index
FROM nav.navigator_items_ordered
LIMIT $Top;
"@ | Set-Content -Encoding UTF8 $tmp
& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmp
