param(
  [Parameter(Mandatory=$true)][string]$RunID,
  [Parameter(Mandatory=$true)][string]$StrategyID,
  [Parameter(Mandatory=$true)][string]$EntryTs,
  [Parameter(Mandatory=$true)][ValidateSet('long','short')][string]$Side,
  [Parameter(Mandatory=$true)][double]$Price,
  [Parameter(Mandatory=$true)][double]$Qty,
  [double]$PnlPct,
  [string]$MetaJson = "{}",
  [switch]$MarkRoadmapDone,
  [string]$TaskCode = "",
  [string]$ChangedBy = "automation"
)

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "Record session: RunID=$RunID, Strategy=$StrategyID, Task=$TaskCode" -ForegroundColor Cyan

# Insert/Upsert trade via SQL here-doc into tradlab_postgres
docker exec -i tradlab_postgres psql -U tradlab -d tradlab_db --set=run_id="$RunID" --set=strategy_id="$StrategyID" --set=entry_ts="$EntryTs" --set=side="$Side" --set=price="$Price" --set=qty="$Qty" --set=pnl_pct="$($PnlPct -as [string])" --set=meta_json="$MetaJson" -f - <<'PSQL'
INSERT INTO lab.trades (
  run_id, strategy_id, entry_ts, side, price, qty, pnl_pct, meta, created_at
) VALUES (
  :'run_id', :'strategy_id', :'entry_ts'::timestamptz, :'side',
  :'price'::double precision, :'qty'::double precision,
  CASE WHEN :'pnl_pct' = '' THEN NULL ELSE :'pnl_pct'::double precision END,
  (CASE WHEN :'meta_json' = '' THEN '{}' ELSE :'meta_json'::jsonb END),
  NOW()
)
ON CONFLICT (run_id, entry_ts, strategy_id, side)
DO UPDATE SET
  price = EXCLUDED.price,
  qty = EXCLUDED.qty,
  pnl_pct = COALESCE(EXCLUDED.pnl_pct, lab.trades.pnl_pct),
  meta = COALESCE(lab.trades.meta, '{}'::jsonb) || COALESCE(EXCLUDED.meta, '{}'::jsonb),
  updated_at = NOW()
RETURNING id, run_id, strategy_id, entry_ts, side;
PSQL

if ($LASTEXITCODE -ne 0) { Write-Host "Error writing trade" -ForegroundColor Red; exit 1 }

# Upsert minimal summary in lab.results
$insertResultSql = @"
INSERT INTO lab.results (run_id, meta, created_at)
VALUES ('$RunID', '{}'::jsonb, NOW())
ON CONFLICT (run_id) DO UPDATE
  SET meta = lab.results.meta || EXCLUDED.meta,
      updated_at = NOW();
"@
docker exec -i tradlab_postgres psql -U tradlab -d tradlab_db -c $insertResultSql | Out-Null

# Log session event into eng_it.roadmap_events (CRD12)
$metaEsc = $MetaJson -replace "'", "''"
$logSql = @"
INSERT INTO eng_it.roadmap_events (entity_type, entity_id, event_type, old_value, new_value, changed_by, meta, ts)
VALUES ('task', NULL, 'session_record', '{}'::jsonb, '{}'::jsonb, '$ChangedBy', '$($metaEsc)'::jsonb, NOW());
"@
docker exec -i crd12_pgvector psql -U crd_user -d crd12 -c $logSql | Out-Null

# Optionally mark roadmap task done
if ($MarkRoadmapDone -and $TaskCode) {
  .\Update-Progress.ps1 -TaskCode $TaskCode -Status 'done' -Description "Automated: session $RunID - DB optimization and trades recorded"
}

Write-Host "`n✅ Done. Regenerate context: .\End-Session.ps1 -Domain TL" -ForegroundColor Green