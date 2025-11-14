param(
  [Parameter(ParameterSetName="ById")]   [string]$ItemId,
  [Parameter(ParameterSetName="ByTitle")][string]$TitleLike,
  [string]$VersionTag = ("RM-{0}-auto" -f (Get-Date -Format yyyyMMdd)),
  [ValidateSet("append","edit","reorder","status_update")] [string]$DiffType = "edit",
  [string]$Title, [string]$Summary, [string]$Deliverable,
  [ValidateSet("planned","in_progress","blocked","done")] [string]$Status,
  [ValidateSet("bot","engineer_b","user","mixed")] [string]$Owner,
  [int]$Priority, [int]$OrderIndex,
  [string[]]$TechHints = @(),
  [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin",
  [string]$Host="localhost",[int]$Port=5433,[string]$Db="crd12",[string]$User="crd_user",[string]$Password="crd12"
)
$ErrorActionPreference="Stop"
$psql = Join-Path $PgBin 'psql.exe'
$env:PGPASSWORD=$Password; $env:PGCLIENTENCODING='UTF8'

# 1) Определить item_id
if(-not $ItemId){
  if(-not $TitleLike){ throw "Укажите -ItemId или -TitleLike" }
  $ItemId = & $psql -At -h $Host -p $Port -U $User -d $Db -c "SELECT item_id FROM nav.roadmap_items WHERE title ILIKE '%$TitleLike%' ORDER BY created_at DESC LIMIT 1;"
  $ItemId = $ItemId.Trim()
  if([string]::IsNullOrWhiteSpace($ItemId)){ throw "Roadmap item не найден по TitleLike='$TitleLike'" }
}

# 2) Собрать fields только из переданных параметров
$fields = @{}
if($PSBoundParameters.ContainsKey('Title'))       { $fields.title       = $Title }
if($PSBoundParameters.ContainsKey('Summary'))     { $fields.summary     = $Summary }
if($PSBoundParameters.ContainsKey('Deliverable')) { $fields.deliverable = $Deliverable }
if($PSBoundParameters.ContainsKey('Status'))      { $fields.status      = $Status }
if($PSBoundParameters.ContainsKey('Owner'))       { $fields.owner       = $Owner }
if($PSBoundParameters.ContainsKey('Priority'))    { $fields.priority    = $Priority }
if($PSBoundParameters.ContainsKey('OrderIndex'))  { $fields.order_index = $OrderIndex }
if($PSBoundParameters.ContainsKey('TechHints') -and $TechHints.Count -gt 0){ $fields.tech_hints = $TechHints }

if($fields.Count -eq 0){ throw "Не переданы поля для правки. Укажите хотя бы один из: -Status -Priority -OrderIndex -Title -Summary -Deliverable -Owner -TechHints" }

# 3) Записать markdown payload
$rev=[guid]::NewGuid().Guid
$mdRel = "workspace/roadmap/revisions/$rev.md"
$mdAbs = Join-Path "C:\Users\Artur\Documents\CRD12" ("workspace\roadmap\revisions\{0}.md" -f $rev)
$md = @"
# Revision $rev
item_id: $ItemId
version_tag: $VersionTag
diff_type: $DiffType
fields: $(($fields | ConvertTo-Json -Depth 5))
"@
$md | Set-Content -Encoding UTF8 $mdAbs

# 4) Событие revision.submitted
$sql = @"
INSERT INTO core.events (ts, source, type, job_id, payload)
VALUES (
  NOW(),'bot','roadmap.revision.submitted',NULL,
  jsonb_build_object(
    'revision_id','$rev',
    'item_id','$ItemId',
    'version_tag','$VersionTag',
    'diff_type','$DiffType',
    'payload_md_ref','$mdRel',
    'fields', $$(SELECT $$ || ($fields | ConvertTo-Json -Depth 5).Replace('"','\"') || $$)$$::jsonb
  )
);
SELECT 'submitted_revision' AS step, '$rev' AS revision_id, '$ItemId' AS item_id;
"@
$tmp=Join-Path $env:TEMP ("roadmap_edit_{0}.sql" -f ([guid]::NewGuid().Guid))
$sql | Set-Content -Encoding UTF8 $tmp
& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmp
Write-Host "✅ Draft-ревизия создана: $mdAbs`nrevision_id: $rev" -ForegroundColor Green
