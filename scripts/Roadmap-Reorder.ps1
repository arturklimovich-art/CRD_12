param(
  [Parameter(ParameterSetName="ById",Mandatory=$true)]   [string]$ItemId,
  [Parameter(ParameterSetName="ByTitle",Mandatory=$true)][string]$TitleLike,
  [Parameter(Mandatory=$true)][int]$OrderIndex,
  [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin",
  [string]$Host="localhost",[int]$Port=5433,[string]$Db="crd12",[string]$User="crd_user",[string]$Password="crd12"
)
$ErrorActionPreference="Stop"
$psql = Join-Path $PgBin 'psql.exe'
$env:PGPASSWORD=$Password; $env:PGCLIENTENCODING='UTF8'

# Определяем item_id по заголовку при необходимости
if($PSCmdlet.ParameterSetName -eq 'ByTitle'){
  $ItemId = (& $psql -At -h $Host -p $Port -U $User -d $Db -c "SELECT item_id FROM nav.roadmap_items WHERE title ILIKE '%$TitleLike%' ORDER BY created_at DESC LIMIT 1;").Trim()
  if([string]::IsNullOrWhiteSpace($ItemId)){ throw "Roadmap item не найден по TitleLike='$TitleLike'" }
}

$sql = @"
INSERT INTO core.events (ts, source, type, job_id, payload)
VALUES (NOW(),'bot','roadmap.item.reordered',NULL, jsonb_build_object(
  'item_id','$ItemId','order_index',$OrderIndex
));
SELECT nav.project_roadmap_catchup() AS last_applied_event_id;
SELECT item_id,title,order_index FROM nav.roadmap_items WHERE item_id='$ItemId';
"@
$tmp=Join-Path $env:TEMP ('reorder_{0}.sql' -f ([guid]::NewGuid().Guid))
$sql | Set-Content -Encoding UTF8 $tmp
& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmp
