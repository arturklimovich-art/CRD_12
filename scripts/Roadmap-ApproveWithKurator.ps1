param(
    [Parameter(Mandatory=$true)]
    [string]$RevisionId,
    
    [string]$ApprovedBy = "user",
    
    [string]$DbHost = "127.0.0.1",
    [int]$Port = 5433,
    [string]$Database = "crd12",
    [string]$User = "crd_user",
    [string]$Password = "crd12",
    [string]$PgBin = "C:\Program Files\PostgreSQL\15\bin"
)

$ErrorActionPreference = "Stop"
$psql = Join-Path $PgBin 'psql.exe'
$env:PGPASSWORD = $Password
$env:PGCLIENTENCODING = 'UTF8'

Write-Host "🚀 Процесс утверждения ревизии с проверкой Kurator" -ForegroundColor Magenta
Write-Host "Ревизия: $RevisionId" -ForegroundColor Cyan

# Шаг 1: Проверка Kurator
Write-Host "`n1. 🔍 Выполняем проверки Kurator..." -ForegroundColor Yellow

$kuratorResult = & $psql -h $DbHost -p $Port -U $User -d $Database -At -c "
SELECT COUNT(*) 
FROM nav.kurator_check_roadmap_revision_simple(
    '$RevisionId',
    (SELECT item_id FROM nav.roadmap_revisions WHERE revision_id = '$RevisionId'),
    (SELECT diff_type FROM nav.roadmap_revisions WHERE revision_id = '$RevisionId'),
    (SELECT payload_md_ref FROM nav.roadmap_revisions WHERE revision_id = '$RevisionId')
)
WHERE severity = 'blocking' AND check_passed = false;"

if ([int]$kuratorResult -gt 0) {
    Write-Host "❌ Kurator: обнаружены блокирующие ошибки! Ревизия не может быть утверждена." -ForegroundColor Red
    
    # Показываем детали ошибок
    $errorDetails = & $psql -h $DbHost -p $Port -U $User -d $Database -c "
    SELECT policy_name, message
    FROM nav.kurator_check_roadmap_revision_simple(
        '$RevisionId',
        (SELECT item_id FROM nav.roadmap_revisions WHERE revision_id = '$RevisionId'),
        (SELECT diff_type FROM nav.roadmap_revisions WHERE revision_id = '$RevisionId'),
        (SELECT payload_md_ref FROM nav.roadmap_revisions WHERE revision_id = '$RevisionId')
    )
    WHERE severity = 'blocking' AND check_passed = false;"
    
    Write-Host "Детали ошибок:" -ForegroundColor Red
    Write-Host $errorDetails
    exit 1
}

Write-Host "✅ Kurator: все проверки пройдены успешно!" -ForegroundColor Green

# Шаг 2: Утверждение ревизии
Write-Host "`n2. ✅ Утверждаем ревизию..." -ForegroundColor Yellow

# Создаем событие roadmap.revision.approved
$sql = @"
INSERT INTO core.events(ts, source, type, job_id, payload)
VALUES (
    NOW(),
    'bot',
    'roadmap.revision.approved',
    NULL,
    jsonb_build_object(
        'revision_id', '$RevisionId',
        'approved_by', '$ApprovedBy'
    )
);
SELECT nav.project_roadmap_catchup();
"@

$tmpFile = Join-Path $env:TEMP "approve_$([guid]::NewGuid().Guid).sql"
$sql | Set-Content -Encoding UTF8 $tmpFile

& $psql -h $DbHost -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 -f $tmpFile
Remove-Item $tmpFile

Write-Host "✅ Ревизия $RevisionId утверждена пользователем $ApprovedBy" -ForegroundColor Green

# Шаг 3: Обновляем материализованное представление
Write-Host "`n3. 🔄 Обновляем roadmap_tree_view..." -ForegroundColor Yellow
.\scripts\Roadmap-RefreshTreeView.ps1 -DbHost $DbHost -Port $Port -Database $Database -User $User -Password $Password

Write-Host "`n🎉 Процесс утверждения завершен успешно!" -ForegroundColor Green
