# Test Utilities for Roadmap Manager
param(
    [string]$DbHost = "127.0.0.1",
    [int]$Port = 5433,
    [string]$Database = "crd12",
    [string]$User = "crd_user",
    [string]$Password = "crd12"
)

$ErrorActionPreference = "Stop"
$psql = "C:\Program Files\PostgreSQL\15\bin\psql.exe"
$env:PGPASSWORD = $Password
$env:PGCLIENTENCODING = 'UTF8'

function Invoke-TestQuery {
    param([string]$Query)
    & $psql -h $DbHost -p $Port -U $User -d $Database -At -c $Query
}

function Get-TestData {
    param([string]$Table, [string]$Where = "")
    
    $query = "SELECT COUNT(*) FROM $Table"
    if ($Where) { $query += " WHERE $Where" }
    
    return [int](Invoke-TestQuery $query)
}

function Clear-TestData {
    Write-Host "🧹 Очистка тестовых данных..." -ForegroundColor Yellow
    
    # Удаляем тестовые данные, но сохраняем системные
    & $psql -h $DbHost -p $Port -U $User -d $Database -c "
    DELETE FROM nav.kurator_checks WHERE checked_by LIKE 'test%';
    DELETE FROM core.jobs WHERE job_id LIKE 'test%';
    DELETE FROM nav.roadmap_revisions WHERE revision_id::text LIKE 'test%';
    DELETE FROM nav.roadmap_items WHERE item_id::text LIKE 'test%';
    DELETE FROM core.events WHERE source = 'test';"
    
    Write-Host "✅ Тестовые данные очищены" -ForegroundColor Green
}

function New-TestItem {
    param([string]$Title, [string]$Status = "planned")
    
    $itemId = "test-item-" + [guid]::NewGuid().Guid.Substring(0, 8)
    
    & $psql -h $DbHost -p $Port -U $User -d $Database -c "
    INSERT INTO core.events(ts, source, type, payload) VALUES (
        NOW(), 'test', 'roadmap.item.created',
        jsonb_build_object(
            'item_id', '$itemId',
            'title', '$Title',
            'summary', 'Test item for acceptance testing',
            'tech_hints', '[""postgresql"", ""powershell""]',
            'deliverable', 'Test deliverable',
            'priority', 3,
            'status', '$Status',
            'owner', 'bot',
            'order_index', 999
        )
    );
    SELECT nav.project_roadmap_catchup();
    "
    
    return $itemId
}

function Write-TestResult {
    param([string]$TestName, [bool]$Passed, [string]$Message)
    
    $color = if ($Passed) { "Green" } else { "Red" }
    $symbol = if ($Passed) { "✅" } else { "❌" }
    
    Write-Host "$symbol $TestName : $Message" -ForegroundColor $color
    return $Passed
}



