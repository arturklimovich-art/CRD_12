param(
    [Parameter(Mandatory=$true)]
    [string]$RevisionId,
    
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

Write-Host "🔍 Kurator: проверка ревизии $RevisionId..." -ForegroundColor Yellow

# Получаем данные ревизии для проверки
$revisionData = & $psql -h $DbHost -p $Port -U $User -d $Database -At -c "
SELECT 
    ri.item_id,
    rr.diff_type,
    rr.payload_md_ref
FROM nav.roadmap_revisions rr
JOIN nav.roadmap_items ri ON rr.item_id = ri.item_id
WHERE rr.revision_id = '$RevisionId';"

if ([string]::IsNullOrWhiteSpace($revisionData)) {
    throw "Ревизия $RevisionId не найдена"
}

$dataParts = $revisionData -split '\|'
$itemId = $dataParts[0].Trim()
$diffType = $dataParts[1].Trim()
$payloadMdRef = $dataParts[2].Trim()

Write-Host "📋 Данные ревизии: item_id=$itemId, diff_type=$diffType, payload_md_ref=$payloadMdRef" -ForegroundColor Cyan

# Выполняем проверки Kurator
Write-Host "✅ Выполняем проверки Kurator..." -ForegroundColor Yellow

$checkResults = & $psql -h $DbHost -p $Port -U $User -d $Database -c "
SELECT 
    policy_name,
    check_passed,
    message,
    severity
FROM nav.kurator_check_roadmap_revision_simple(
    '$RevisionId',
    '$itemId',
    '$diffType',
    '$payloadMdRef'
);"

Write-Host "`n📊 Результаты проверок Kurator:" -ForegroundColor Magenta
Write-Host $checkResults

# Проверяем наличие блокирующих ошибок
$blockingErrors = & $psql -h $DbHost -p $Port -U $User -d $Database -At -c "
SELECT COUNT(*) 
FROM nav.kurator_check_roadmap_revision_simple(
    '$RevisionId',
    '$itemId',
    '$diffType',
    '$payloadMdRef'
)
WHERE severity = 'blocking' AND check_passed = false;"

if ([int]$blockingErrors -gt 0) {
    Write-Host "❌ Kurator: обнаружены блокирующие ошибки! Ревизия не может быть утверждена." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Kurator: все проверки пройдены успешно!" -ForegroundColor Green

# Сохраняем результаты проверок в БД
& $psql -h $DbHost -p $Port -U $User -d $Database -c "
INSERT INTO nav.kurator_checks (policy_id, target_type, target_id, check_passed, check_message, checked_by)
SELECT 
    p.policy_id,
    'roadmap_revision',
    '$RevisionId',
    k.check_passed,
    k.message,
    'kurator_script'
FROM nav.kurator_check_roadmap_revision_simple(
    '$RevisionId',
    '$itemId',
    '$diffType',
    '$payloadMdRef'
) k
JOIN nav.kurator_policies p ON k.policy_name = p.policy_name;"

Write-Host "📝 Результаты проверок сохранены в nav.kurator_checks" -ForegroundColor Cyan
