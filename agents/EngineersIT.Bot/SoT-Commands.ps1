# ============================================================================
# agents/EngineersIT.Bot/SoT-Commands.ps1
# PowerShell ??????? ??? ?????? ? Source of Truth (SoT)
# ??????: E1-B0-T3-S2
# ?????: arturklimovich-art
# ????: 2025-11-23 18:08:00 UTC
# ============================================================================

$Global:SoT_Container = "crd12_engineer_b_api"
$Global:SoT_PythonPath = "/app/src/engineer_b_api/sot"

function Sync-CoreCatalog {
    Write-Host "?? ????????????? Core-???????? ???????..." -ForegroundColor Cyan
    
    $result = docker exec $Global:SoT_Container python -c @"
import sys
sys.path.insert(0, '/app/src/engineer_b_api')
from pathlib import Path
from sot.yaml_sync import YAMLSyncEngine

db_dsn = 'postgresql://crd_user:crd12@crd12_pgvector:5432/crd12'
engine = YAMLSyncEngine(db_dsn, Path('/app'))
result = engine.sync_core_catalog()
engine.close()

print(f\"Status: {result['status']}\")
print(f\"Domains synced: {result.get('domains_synced', 0)}\")
if result.get('changes'):
    print(\"Changes:\")
    for change in result['changes']:
        print(f\"  - {change}\")
if 'error' in result:
    print(f\"Error: {result['error']}\")
"@
    
    Write-Host $result
    
    if ($result -match "Status: success") {
        Write-Host "? ????????????? ????????? ???????" -ForegroundColor Green
        return $true
    } else {
        Write-Host "? ?????? ?????????????" -ForegroundColor Red
        return $false
    }
}

function Get-Domain {
    param(
        [Parameter(Mandatory=$true)]
        [string]$DomainCode
    )
    
    Write-Host "?? ????????? ?????????? ? ??????: $DomainCode" -ForegroundColor Cyan
    
    $query = "SELECT * FROM eng_it.sot_domains WHERE code = '$DomainCode';"
    $result = $query | docker exec -i crd12_pgvector psql -U crd_user -d crd12 -t
    
    if ($result) {
        Write-Host $result -ForegroundColor White
        return $true
    } else {
        Write-Host "? ????? ?? ??????" -ForegroundColor Red
        return $false
    }
}

function Get-AllDomains {
    Write-Host "?? ?????? ???????:" -ForegroundColor Cyan
    
    $query = @"
SELECT 
    code, 
    title, 
    status, 
    plan_path,
    to_char(updated_at, 'YYYY-MM-DD HH24:MI:SS') as last_update
FROM eng_it.sot_domains 
ORDER BY code;
"@
    
    $query | docker exec -i crd12_pgvector psql -U crd_user -d crd12
}

function Get-SyncHistory {
    param(
        [int]$Limit = 10
    )
    
    Write-Host "?? ??????? ????????????? (????????? $Limit ???????):" -ForegroundColor Cyan
    
    $query = @"
SELECT 
    id,
    COALESCE(domain_code, 'CORE') as domain,
    sync_type,
    status,
    to_char(last_synced, 'YYYY-MM-DD HH24:MI:SS') as synced_at,
    COALESCE(error_msg, '-') as error
FROM eng_it.sot_sync 
ORDER BY last_synced DESC 
LIMIT $Limit;
"@
    
    $query | docker exec -i crd12_pgvector psql -U crd_user -d crd12
}

Export-ModuleMember -Function @(
    'Sync-CoreCatalog',
    'Get-Domain',
    'Get-AllDomains',
    'Get-SyncHistory'
)

Write-Host "? SoT-Commands ?????????" -ForegroundColor Green
