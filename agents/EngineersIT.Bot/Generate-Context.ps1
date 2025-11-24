Write-Host "Generating CRD12 context..." -ForegroundColor Cyan
$dt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"# CRD12 CONTEXT - $dt UTC

Repository: github.com/arturklimovich-art/CRD_12
Branch: feature/roadmap-arturklimovich-20251117

## Database
- Host: localhost:5432
- Database: crd12
- Schema: eng_it
- Blocks: 26
- Tasks: 63
- Steps: 14

## Completed
- E1-B0-T1: DB schema (done)
- E1-B0-T2: Migrations (done)
- E1-B0-T3: YAML sync (done)
- E1-B0-T4: Roadmap parsing (done)
- TL Quick Start (done)

## Next Tasks
- E1-B0-T5: Reverse sync (DB to YAML)
- TL-B2: OHLCV database
- TL-B4: Advanced backtest

## Files
- ROADMAP/DOMAINS/ENG/GENERAL_PLAN.yaml
- ROADMAP/DOMAINS/TL/GENERAL_PLAN.yaml
- src/engineer_b_api/sot/yaml_sync.py

---
What task are we working on today?
" | Out-File -Encoding UTF8 "CHAT_CONTEXT.txt"
Write-Host "Done! Context saved to CHAT_CONTEXT.txt" -ForegroundColor Green
notepad CHAT_CONTEXT.txt

