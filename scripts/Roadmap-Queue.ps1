param(
  [string]$TzPath,                    # например: C:\Users\Artur\Documents\CRD12\workspace\roadmap\tz\*.json
  [string]$TzId,
  [string]$TitleLike,                 # альтернатива: взять item по заголовку, затем найти последнее ТЗ
  [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin",
  [string]$Host="localhost",[int]$Port=5433,[string]$Db="crd12",[string]$User="crd_user",[string]$Password="crd12"
)
$ErrorActionPreference="Stop"
$psql = Join-Path $PgBin 'psql.exe'
$env:PGPASSWORD=$Password; $env:PGCLIENTENCODING='UTF8'
$base="C:\Users\Artur\Documents\CRD12"

function Resolve-TZ {
  param([string]$TzPath,[string]$TzId,[string]$TitleLike)
  if($TzPath){
    if(-not(Test-Path $TzPath)){ throw "Не найден файл: $TzPath" }
    return Get-Item $TzPath | Select-Object -ExpandProperty FullName
  }
  if($TzId){
    $p = Join-Path $base ("workspace\roadmap\tz\{0}.json" -f $TzId)
    if(-not(Test-Path $p)){ throw "ТЗ по TzId не найдено: $p" }
    return $p
  }
  if($TitleLike){
    $itemId = (& $psql -At -h $Host -p $Port -U $User -d $Db -c "SELECT item_id FROM nav.roadmap_items WHERE title ILIKE '%$TitleLike%' ORDER BY created_at DESC LIMIT 1;").Trim()
    if([string]::IsNullOrWhiteSpace($itemId)){ throw "Roadmap item не найден по TitleLike='$TitleLike'" }
    $cand = Get-ChildItem (Join-Path $base 'workspace\roadmap\tz') -Filter *.json | Sort-Object LastWriteTime -Descending | ForEach-Object {
      $j = Get-Content -Raw -Encoding UTF8 $_.FullName | ConvertFrom-Json
      if($j.source_item_id -eq $itemId){ return $_.FullName }
    } | Select-Object -First 1
    if(-not $cand){ throw "Не найдено ТЗ для item_id=$itemId" }
    return $cand
  }
  throw "Укажите один из параметров: -TzPath | -TzId | -TitleLike"
}

$tzFile = Resolve-TZ -TzPath $TzPath -TzId $TzId -TitleLike $TitleLike
$tz = Get-Content -Raw -Encoding UTF8 $tzFile | ConvertFrom-Json

# обязательные поля контракта
$tz_id = $tz.tz_id
$item  = $tz.source_item_id
$exec  = $tz.executor
$idem  = if($tz.idempotency_key){ $tz.idempotency_key } else { $tz_id }
$corr  = if($tz.correlation_id){ $tz.correlation_id } else { $tz_id }
$rel   = if($tz.tz_path){ $tz.tz_path } else { "workspace/roadmap/tz/$tz_id.json" }
if([string]::IsNullOrWhiteSpace($tz_id) -or [string]::IsNullOrWhiteSpace($item)){ throw "Некорректный JSON ТЗ: tz_id/source_item_id пустые" }

# job_id
$jobId = "job_{0}" -f $tz_id.Substring(0,8)

# SQL: вставить job (если нет) и событие bot.tz.queued
$sql = @"
-- ensure job uniqueness by job_id
INSERT INTO core.jobs(job_id,created_at,status,source,task_type,meta)
SELECT '$jobId', NOW(),'pending','bot','engineer_tz',
       jsonb_build_object('tz_id','$tz_id','item_id','$item','tz_path','$rel','executor','$exec','idempotency_key','$idem','correlation_id','$corr')
WHERE NOT EXISTS (SELECT 1 FROM core.jobs WHERE job_id='$jobId');

INSERT INTO core.events(ts,source,type,job_id,payload)
VALUES (NOW(),'bot','bot.tz.queued','$jobId', jsonb_build_object('tz_id','$tz_id','item_id','$item','executor','$exec'));

-- показать связку в навигаторе
SELECT job_id, task_type, job_status, title, roadmap_status, item_id
FROM nav.navigator_tasks_link
WHERE job_id = '$jobId';
"@
$tmp = Join-Path $env:TEMP ('queue_tz_{0}.sql' -f ([guid]::NewGuid().Guid))
$sql | Set-Content -Encoding UTF8 $tmp
& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmp

Write-Host ("✅ Поставлено в очередь: {0}`n    ТЗ: {1}" -f $jobId,$tzFile) -ForegroundColor Green
