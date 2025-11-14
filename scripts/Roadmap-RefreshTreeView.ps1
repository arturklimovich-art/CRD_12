param(
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

Write-Host "🔄 Обновление материализованного представления roadmap_tree_view..." -ForegroundColor Yellow

# Выполняем обновление представления
& $psql -h $DbHost -p $Port -U $User -d $Database -c "REFRESH MATERIALIZED VIEW nav.roadmap_tree_view;"

Write-Host "✅ Материализованное представление roadmap_tree_view обновлено" -ForegroundColor Green

# Проверяем количество записей
$count = & $psql -h $DbHost -p $Port -U $User -d $Database -At -c "SELECT COUNT(*) FROM nav.roadmap_tree_view;"
Write-Host "📊 Записей в представлении: $count" -ForegroundColor Cyan
