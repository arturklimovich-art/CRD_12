param(
  [string]$DbHost = "127.0.0.1",
  [int]$Port = 5433,
  [string]$Database = "crd12",
  [string]$User = "crd_user",
  [string]$Password = "crd12",
  [Parameter(ParameterSetName="ById")]   [string]$ItemId,
  [Parameter(ParameterSetName="ByTitle")][string]$TitleLike,
  [Parameter(Mandatory=$true)][ValidateSet("planned","in_progress","blocked","done")] [string]$Status,
  [string]$ApprovedBy="user",
  [string]$PgBin="C:\Program Files\PostgreSQL\15\bin"
)
$ErrorActionPreference = "Stop"
$psql = Join-Path $PgBin 'psql.exe'
$env:PGPASSWORD=$Password; $env:PGCLIENTENCODING='UTF8'

# 1) Определяем item_id
if(-not $ItemId){
  if(-not $TitleLike){ throw "Укажите -ItemId или -TitleLike" }
  $ItemId = & $psql -At -h \$DbHost -p $Port -U $User -d \$Database -c "SELECT item_id FROM nav.roadmap_items WHERE title ILIKE '%$TitleLike%' ORDER BY created_at DESC LIMIT 1;"
  $ItemId = $ItemId.Trim()
  if([string]::IsNullOrWhiteSpace($ItemId)){ throw "Roadmap item не найден по TitleLike='$TitleLike'" }
}

# 2) Готовим ревизию (markdown payload)
$rev=[guid]::NewGuid().Guid
$mdRel="workspace/roadmap/revisions/$rev.md"
$mdAbs=Join-Path "C:\Users\Artur\Documents\CRD12" ("workspace\roadmap\revisions\{0}.md" -f $rev)
@"
# Revision $rev
item_id: $ItemId
version_tag: RM-$(Get-Date -Format yyyyMMdd)-status
diff_type: edit
fields: { ""status"": ""$Status"" }
"@ | Set-Content -Encoding UTF8 $mdAbs

# 3) События submitted -> approved + catch-up
$sql=@"
INSERT INTO core.events(ts,source,type,job_id,payload)
VALUES (NOW(),'bot','roadmap.revision.submitted',NULL,
        jsonb_build_object(
          'revision_id','$rev','item_id','$ItemId',
          'version_tag','RM-$(Get-Date -Format yyyyMMdd)-status',
          'diff_type','edit','payload_md_ref','$mdRel',
          'fields', jsonb_build_object('status','$Status')
        ));
INSERT INTO core.events(ts,source,type,job_id,payload)
VALUES (NOW(),'bot','roadmap.revision.approved',NULL,
        jsonb_build_object(
          'revision_id','$rev','item_id','$ItemId',
          'approved_by','$ApprovedBy',
          'fields', jsonb_build_object('status','$Status')
        ));
SELECT nav.project_roadmap_catchup() AS last_applied_event_id;
SELECT item_id,title,status,active_revision_id FROM nav.roadmap_items WHERE item_id='$ItemId';
"@
$tmp=Join-Path $env:TEMP ('set_status_{0}.sql' -f ([guid]::NewGuid().Guid))
$sql | Set-Content -Encoding UTF8 $tmp
& $psql -h \$DbHost -p $Port -U $User -d \$Database -v ON_ERROR_STOP=1 -f $tmp
Write-Host "✅ Статус обновлён событиями. Revision: $rev`nФайл: $mdAbs" -ForegroundColor Green







# Автообновление системного слепка
& 'C:\Users\Artur\Documents\CRD12\scripts\System-Snapshot-Auto.ps1' -Reason 'status_changed'

