param(
  [Parameter(ParameterSetName="ById")]   [string]$ItemId,
  [Parameter(ParameterSetName="ByTitle")][string]$TitleLike,
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

# 2) Загрузить поля roadmap-item
$q = @"
SELECT title, summary, tech_hints::text, deliverable, priority, status
FROM nav.roadmap_items WHERE item_id='$ItemId' LIMIT 1;
"@
$r = & $psql -At -h $Host -p $Port -U $User -d $Db -c $q
if([string]::IsNullOrWhiteSpace($r)){ throw "ItemId '$ItemId' не найден в nav.roadmap_items" }
$parts = $r -split '\|'
$title=$parts[0]; $summary=$parts[1]; $tech_json=$parts[2]; $deliver=$parts[3]; $prio=$parts[4]; $status=$parts[5]

# 3) Сборка ТЗ (контракт v1)
$tzId=[guid]::NewGuid().Guid
$corr=$tzId; $idem=$tzId
$tzDir="C:\Users\Artur\Documents\CRD12\workspace\roadmap\tz"
New-Item -ItemType Directory -Force -Path $tzDir | Out-Null
$tzRel="workspace/roadmap/tz/$tzId.json"
$tzAbs=Join-Path $tzDir "$tzId.json"

# шаги по умолчанию
$steps = @(
  @{ title='Контекст и цели'; details="Осмыслить summary/deliverable из Roadmap и стандарты S-0/DoD проекта." },
  @{ title='Декомпозиция';    details="Разбить задачу на проверяемые шаги с критериями приёмки и откатом." },
  @{ title='Реализация';      details="Выполнить миграции/код/тесты строго в зелёных путях проекта." },
  @{ title='Смоук-тест';      details="Проверки структур, логов событий и навигатора." }
)

# тех-хинты
try { $tech = if([string]::IsNullOrWhiteSpace($tech_json)) { @() } else { ($tech_json | ConvertFrom-Json) } } catch { $tech=@() }

$tz = [ordered]@{
  tz_id = $tzId
  title = $title
  description = if($summary){ $summary } else { 'Детализировать и выполнить по стандартам проекта.' }
  acceptance_criteria = @(
    'Соблюдены контракт данных/пути проекта',
    'Операции только через события/очереди, без прямого CRUD в проекциях',
    'Есть план отката и смоук-тесты'
  )
  artifacts = @()
  tech_stack = @('PowerShell','PostgreSQL','PL/pgSQL') + $tech
  steps = $steps
  executor = 'Engineer_B'
  priority = [int]$prio
  deadline_iso = $null
  idempotency_key = $idem
  correlation_id = $corr
  source_item_id = $ItemId
  tz_path = $tzRel
}

$tz | ConvertTo-Json -Depth 7 | Set-Content -Encoding UTF8 $tzAbs

# 4) Событие bot.tz.generated (append-only)
$sql=@"
INSERT INTO core.events(ts,source,type,job_id,payload)
VALUES (NOW(),'bot','bot.tz.generated',NULL,
        jsonb_build_object('tz_id','$tzId','item_id','$ItemId','tz_path','$tzRel','executor','Engineer_B'));
SELECT 'tz_generated' AS step, '$tzRel' AS tz_path;
"@
$tmp=Join-Path $env:TEMP ('gen_tz_{0}.sql' -f ([guid]::NewGuid().Guid))
$sql | Set-Content -Encoding UTF8 $tmp
& $psql -h $Host -p $Port -U $User -d $Db -v ON_ERROR_STOP=1 -f $tmp

Write-Host "✅ Сгенерировано ТЗ: $tzAbs" -ForegroundColor Green
