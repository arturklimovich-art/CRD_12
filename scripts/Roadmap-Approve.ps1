param(
  [string]$RevisionId,
  [string]$TitleLike,
  [string]$ApprovedBy = "user",
  [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin",
  [string]$Host="localhost",[int]$Port=5433,[string]$Db="crd12",[string]$User="crd_user",[string]$Password="crd12"
)
$ErrorActionPreference="Stop"
if(-not $RevisionId -and -not $TitleLike){ throw "Укажите -RevisionId или -TitleLike" }
$psql = Join-Path $PgBin 'psql.exe'
$env:PGPASSWORD=$Password; $env:PGCLIENTENCODING='UTF8'

# SQL: находим цель (rev,item,fields) либо по RevisionId, либо по TitleLike
$tmp = Join-Path $env:TEMP ('approve_rev_{0}.sql' -f ([guid]::NewGuid().Guid))
$sql = @"
WITH target AS (
  SELECT
    (e.payload->>'revision_id')::uuid AS revision_id,
    (e.payload->>'item_id')::uuid     AS item_id,
    (e.payload->'fields')::jsonb      AS fields
  FROM core.events e
  /** фильтрация цели **/
  WHERE e.type='roadmap.revision.submitted'
  AND (
    /** by explicit revision_id **/
    (@REV IS NOT NULL AND (e.payload->>'revision_id')::uuid = @REV::uuid)
    OR
    /** by TitleLike on nav.roadmap_items **/
    (@REV IS NULL AND EXISTS (
      SELECT 1
      FROM nav.roadmap_items i
      WHERE i.item_id::text = e.payload->>'item_id'
        AND i.title ILIKE @TL
    ))
  )
  ORDER BY e.id DESC
  LIMIT 1
)
INSERT INTO core.events (ts, source, type, job_id, payload)
SELECT NOW(),'bot','roadmap.revision.approved',NULL,
       jsonb_build_object(
         'revision_id', revision_id::text,
         'item_id',     item_id::text,
         'approved_by', @APPROVER,
         'fields',      COALESCE(fields,'{}'::jsonb)
       )
FROM target;

SELECT nav.project_roadmap_catchup() AS last_applied_event_id;
SELECT i.title, i.status, i.active_revision_id
FROM nav.roadmap_items i
JOIN target t ON t.item_id = i.item_id;
"@

# Подстановка параметров безопасно (без PowerShell-экранирования SQL)
$tlike = if([string]::IsNullOrWhiteSpace($TitleLike)) { $null } else { "%$TitleLike%" }
$sql = $sql.Replace('@REV',  (if($RevisionId){ "'" + $RevisionId + "'" } else { 'NULL' }))
$sql = $sql.Replace('@TL',   (if($tlike){ "'" + $tlike.Replace("'","''") + "'" } else { 'NULL' }))
$sql = $sql.Replace('@APPROVER', ("'" + $ApprovedBy.Replace("'","''") + "'"))

$sql | Set-Content -Encoding UTF8 $tmp
& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmp
