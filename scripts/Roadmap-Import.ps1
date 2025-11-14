param(
  [string]$RoadmapPath = "C:\Users\Artur\Documents\CRD12\config\roadmap\Roadmap.md",
  [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin",
  [string]$Host = "localhost", [int]$Port = 5433,
  [string]$Db = "crd12", [string]$User = "crd_user", [string]$Password = "crd12"
)
$ErrorActionPreference="Stop"
if(-not(Test-Path $RoadmapPath)){ throw "Roadmap not found: $RoadmapPath" }
$env:PGPASSWORD=$Password; $env:PGCLIENTENCODING='UTF8'; $psql=Join-Path $PgBin 'psql.exe'
$txt=Get-Content -Raw -Encoding UTF8 $RoadmapPath
$re='- item_id:\s*(?<code>[^\r\n]+)\s*\r?\n\s*title:\s*(?<title>[^\r\n]+)\s*\r?\n\s*status:\s*(?<status>[^\r\n]+)'
$matches=[regex]::Matches($txt,$re,[System.Text.RegularExpressions.RegexOptions]::Multiline)
if($matches.Count -eq 0){ Write-Error "No items parsed from $RoadmapPath"; exit 1 }
$order=10; $buf=@()
foreach($m in $matches){
  $title=$m.Groups['title'].Value.Trim()
  $status=$m.Groups['status'].Value.Trim()
  $uuid=[guid]::NewGuid().Guid
  $buf += @"
INSERT INTO core.events (ts, source, type, job_id, payload)
SELECT NOW(),'bot','roadmap.item.created',NULL,
  jsonb_build_object(
    'item_id',       '$uuid',
    'parent_id',     NULL,
    'title',         '$title',
    'summary',       NULL,
    'tech_hints',    jsonb_build_array(),
    'deliverable',   NULL,
    'priority',      1,
    'status',        '$status',
    'owner',         'bot',
    'order_index',   $order
  )
WHERE NOT EXISTS (SELECT 1 FROM nav.roadmap_items WHERE title = '$title');
"@
  $order+=10
}
$sql = ($buf -join "`n") + "`nSELECT nav.project_roadmap_catchup() AS last_applied_event_id;"
$tmp=Join-Path $env:TEMP ('roadmap_import_{0}.sql' -f ([guid]::NewGuid().Guid))
$sql | Set-Content -Encoding UTF8 $tmp
& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmp
