# ============================================================================
# agents/EngineersIT.Bot/End-Session.ps1 V2 FINAL
# УНИВЕРСАЛЬНАЯ система контекста (ПРАВИЛЬНЫЕ КОЛОНКИ БД)
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [switch]$SkipGit,
    [switch]$SkipClipboard
)

$ErrorActionPreference = "Stop"

# КОДИРОВКА
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PGCLIENTENCODING = "UTF8"
chcp 65001 | Out-Null

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🎯 ЗАВЕРШЕНИЕ СЕССИИ: ДОМЕН $Domain" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$utcTimestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss") + "Z"

# Пути
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$contextDir = Join-Path $projectRoot "context/$Domain"
$sessionFile = "$contextDir/session_$timestamp.md"
$latestFile = "$contextDir/latest.md"

if (-not (Test-Path $contextDir)) {
    New-Item -ItemType Directory -Path $contextDir -Force | Out-Null
}

# ИСТОЧНИК
Write-Host "`n[1/7] Определение источника..." -ForegroundColor Yellow

$ds = @{
    TL = @{
        Name = "TradLab"
        Full = "TradLab Trading System"
        DB = "crd12"
        DBHost = "crd12_pgvector"
        DBUser = "crd_user"
        DBPort = 5433
        DBTable = "eng_it.roadmap_tasks"
        CodePath = "src/tradlab"
        ScriptsPath = "scripts/tradlab"
        ResultsDB = "tradlab_db"
        ResultsHost = "tradlab_postgres"
        ResultsUser = "tradlab"
        ResultsPort = 5434
    }
}

if (-not $ds.ContainsKey($Domain)) {
    Write-Host "[ERROR] Неизвестный домен: $Domain" -ForegroundColor Red
    exit 1
}

$d = $ds[$Domain]
Write-Host "[OK] $($d.Full)" -ForegroundColor Green

# ЗАДАЧИ
Write-Host "`n[2/7] Сбор задач..." -ForegroundColor Yellow

$sql = "SELECT code, title, status, priority, description FROM $($d.DBTable) WHERE domain_code='$Domain' ORDER BY priority, code;"

$taskList = @()
$doneCount = 0
$inProgressCount = 0
$plannedCount = 0

try {
    $tasks = docker exec -i $($d.DBHost) psql -U $($d.DBUser) -d $($d.DB) -t -A -F'|' -c $sql 2>$null
    
    foreach ($line in ($tasks -split "`n")) {
        if ($line.Trim() -and $line -match '\|') {
            $parts = $line.Split('|')
            if ($parts.Count -ge 3) {
                $status = $parts[2].Trim()
                $taskList += @{
                    Code = $parts[0].Trim()
                    Title = $parts[1].Trim()
                    Status = $status
                    Priority = if ($parts.Count -ge 4 -and $parts[3].Trim()) { [int]$parts[3].Trim() } else { 999 }
                    Desc = if ($parts.Count -ge 5) { $parts[4].Trim() } else { "" }
                }
                
                switch ($status) {
                    {$_ -in @('completed', 'done')} { $doneCount++ }
                    {$_ -in @('in_progress', 'in progress')} { $inProgressCount++ }
                    'planned' { $plannedCount++ }
                }
            }
        }
    }
    
    $total = $taskList.Count
    $pct = if ($total -gt 0) { [math]::Round(($doneCount / $total) * 100, 0) } else { 0 }
    
    Write-Host "[OK] Задач: $total | Выполнено: $doneCount ($pct%)" -ForegroundColor Green
    
} catch {
    Write-Host "[WARN] $_" -ForegroundColor Yellow
    $total = 0
    $pct = 0
}

# МЕТРИКИ (ИСПРАВЛЕННЫЕ КОЛОНКИ)
Write-Host "`n[3/7] Сбор метрик..." -ForegroundColor Yellow

$metrics = $null

if ($Domain -eq "TL") {
    # ПРАВИЛЬНЫЕ КОЛОНКИ: pnl_total, sharpe, sortino, max_dd, calmar, win_rate, profit_factor
    $sqlM = "SELECT run_id, pnl_total, sharpe, sortino, max_dd, calmar, win_rate, profit_factor, pass_risk_gate, meta FROM lab.results ORDER BY start_ts DESC LIMIT 1;"
    
    try {
        $mRaw = docker exec -i $($d.ResultsHost) psql -U $($d.ResultsUser) -d $($d.ResultsDB) -t -A -F'|' -c $sqlM 2>$null
        
        if ($mRaw.Trim()) {
            $mp = $mRaw.Split('|')
            if ($mp.Count -ge 8) {
                $pnl = [math]::Round([double]$mp[1].Trim(), 2)
                $sharpe = [math]::Round([double]$mp[2].Trim(), 2)
                $sortino = [math]::Round([double]$mp[3].Trim(), 2)
                $maxdd = [math]::Round([double]$mp[4].Trim(), 2)
                $calmar = [math]::Round([double]$mp[5].Trim(), 2)
                $winrate = [math]::Round([double]$mp[6].Trim(), 2)
                $pf = [math]::Round([double]$mp[7].Trim(), 2)
                $riskGate = if ($mp.Count -ge 9) { $mp[8].Trim() } else { "unknown" }
                
                # Попытка извлечь total_trades и avg_hold из meta (JSON)
                $totalTrades = "N/A"
                $avgHold = "N/A"
                
                if ($mp.Count -ge 10 -and $mp[9].Trim()) {
                    try {
                        $metaJson = $mp[9].Trim() | ConvertFrom-Json
                        if ($metaJson.total_trades) { $totalTrades = $metaJson.total_trades }
                        if ($metaJson.avg_hold_time_hours) { $avgHold = [math]::Round([double]$metaJson.avg_hold_time_hours, 1) }
                    } catch {
                        # Игнорировать ошибки парсинга JSON
                    }
                }
                
                $metrics = @{
                    RunID = $mp[0].Trim()
                    PnL = $pnl
                    Sharpe = $sharpe
                    Sortino = $sortino
                    MaxDD = $maxdd
                    Calmar = $calmar
                    WinRate = $winrate
                    PF = $pf
                    RiskGate = $riskGate
                    Trades = $totalTrades
                    Hold = $avgHold
                }
                Write-Host "[OK] PnL=$($metrics.PnL)%, Sharpe=$($metrics.Sharpe)" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "[WARN] Метрики: $_" -ForegroundColor Yellow
    }
}

# КОД
Write-Host "`n[4/7] Анализ кода..." -ForegroundColor Yellow

$files = @()
$loc = 0

$paths = @($d.CodePath, $d.ScriptsPath) | Where-Object {$_}

foreach ($p in $paths) {
    $fp = Join-Path $projectRoot $p
    if (Test-Path $fp) {
        Get-ChildItem -Path $fp -Recurse -File | 
            Where-Object {$_.Extension -in @('.py', '.ps1', '.sql') -and $_.Name -notmatch '__pycache__|\.pyc$'} |
            ForEach-Object {
                $l = (Get-Content $_.FullName -ErrorAction SilentlyContinue).Count
                $loc += $l
                $files += @{
                    Name = $_.Name
                    Path = $_.FullName -replace [regex]::Escape($projectRoot + '\'), ''
                    LOC = $l
                }
            }
    }
}

Write-Host "[OK] Файлов: $($files.Count) | LOC: $loc" -ForegroundColor Green

# ПРИОРИТЕТЫ
Write-Host "`n[5/7] Приоритеты..." -ForegroundColor Yellow

$next = $taskList | Where-Object {$_.Status -in @('in_progress', 'planned')} | Sort-Object Priority | Select-Object -First 5

Write-Host "[OK] $($next.Count) задач" -ForegroundColor Green

# MARKDOWN
Write-Host "`n[6/7] Формирование..." -ForegroundColor Yellow

$md = @()
$md += "# 📊 $($d.Full) - Session Context"
$md += ""
$md += "**Version:** 2.0"
$md += "**Date:** $utcTimestamp"
$md += "**Domain:** $Domain"
$md += "**Progress:** $pct% ($doneCount/$total tasks)"
$md += ""
$md += "---"
$md += ""
$md += "## 🚀 QUICK START"
$md += ""
$md += '```powershell'
$md += "# 1. Navigate"
$md += "cd `"$projectRoot`""
$md += ""
$md += "# 2. Git status"
$md += "git status"
$md += ""
$md += "# 3. Check progress"
$md += "docker exec -i $($d.DBHost) psql -U $($d.DBUser) -d $($d.DB) -c `"SELECT code, title, status FROM $($d.DBTable) WHERE domain_code='$Domain' LIMIT 10;`""
$md += '```'
$md += ""
$md += "---"
$md += ""
$md += "## 📂 PROJECT ROOT"
$md += ""
$md += '```'
$md += $projectRoot
$md += '```'
$md += ""
$md += "---"
$md += ""
$md += "## 🗄️ DATABASES (CRITICAL!)"
$md += ""
$md += "### Database 1: Roadmap & Core (crd12)"
$md += ""
$md += '```yaml'
$md += "Port: $($d.DBPort)"
$md += "Container: $($d.DBHost)"
$md += "Database: $($d.DB)"
$md += "User: $($d.DBUser)"
$md += "Purpose: Roadmap, tasks, events"
$md += '```'
$md += ""
$md += "**Connection:**"
$md += '```powershell'
$md += "docker exec -i $($d.DBHost) psql -U $($d.DBUser) -d $($d.DB)"
$md += '```'
$md += ""
$md += "⚠️ **DO NOT USE FOR TradLab data!**"
$md += ""

if ($Domain -eq "TL" -and $d.ResultsDB) {
    $md += "### Database 2: TradLab Data (tradlab_db)"
    $md += ""
    $md += '```yaml'
    $md += "Port: $($d.ResultsPort)"
    $md += "Container: $($d.ResultsHost)"
    $md += "Database: $($d.ResultsDB)"
    $md += "User: $($d.ResultsUser)"
    $md += "Password: crd12"
    $md += "Purpose: OHLCV, features, backtests"
    $md += '```'
    $md += ""
    $md += "**Connection:**"
    $md += '```powershell'
    $md += "docker exec -i $($d.ResultsHost) psql -U $($d.ResultsUser) -d $($d.ResultsDB)"
    $md += '```'
    $md += ""
    $md += "**Key Tables:**"
    $md += "- market.ohlcv - OHLCV data"
    $md += "- lab.features_v1 - Feature store"
    $md += "- lab.results - Backtest results"
    $md += "- lab.trades - Individual trades"
    $md += ""
    $md += "⚠️ **USE THIS for all TradLab operations!**"
    $md += ""
}

$md += "**CRITICAL:** TWO SEPARATE databases on DIFFERENT PORTS!"
$md += ""

$md += "---"
$md += ""
$md += "## 📊 STATUS"
$md += ""
$md += "**Statistics:**"
$md += "- Total: $total tasks"
$md += "- Done: $doneCount ($pct%)"
$md += "- In Progress: $inProgressCount"
$md += "- Planned: $plannedCount"
$md += ""

# Группы задач
$done = $taskList | Where-Object {$_.Status -in @('completed', 'done')} | Sort-Object Priority
$inProg = $taskList | Where-Object {$_.Status -in @('in_progress', 'in progress')} | Sort-Object Priority
$plan = $taskList | Where-Object {$_.Status -eq 'planned'} | Sort-Object Priority

if ($done) {
    $md += "### ✅ Completed ($($done.Count))"
    $md += ""
    foreach ($t in $done) {
        $md += "- **$($t.Code)**: $($t.Title)"
    }
    $md += ""
}

if ($inProg) {
    $md += "### 🔄 In Progress ($($inProg.Count))"
    $md += ""
    foreach ($t in $inProg) {
        $md += "- **$($t.Code)**: $($t.Title)"
    }
    $md += ""
}

if ($plan) {
    $md += "### 📋 Planned ($($plan.Count))"
    $md += ""
    foreach ($t in ($plan | Select-Object -First 5)) {
        $md += "- **$($t.Code)**: $($t.Title)"
    }
    $md += ""
}

# МЕТРИКИ
if ($metrics) {
    $md += "---"
    $md += ""
    $md += "## 📈 LATEST PERFORMANCE"
    $md += ""
    $md += '```yaml'
    $md += "Run ID: $($metrics.RunID)"
    $md += "PnL: +$($metrics.PnL)% $(if ($metrics.PnL -gt 0) { '✅' } else { '❌' })"
    $md += "Sharpe: $($metrics.Sharpe) $(if ($metrics.Sharpe -ge 1.0) { '✅' } else { '❌ (target ≥1.0)' })"
    $md += "Sortino: $($metrics.Sortino)"
    $md += "Max DD: $($metrics.MaxDD)%"
    $md += "Calmar: $($metrics.Calmar)"
    $md += "Win Rate: $($metrics.WinRate)%"
    $md += "Profit Factor: $($metrics.PF)"
    $md += "Total Trades: $($metrics.Trades)"
    $md += "Avg Hold Time: $($metrics.Hold)h"
    $md += "Risk Gate: $(if ($metrics.RiskGate -eq 't') { '✅ PASS' } else { '❌ FAIL' })"
    $md += '```'
    $md += ""
}

# КОД
$md += "---"
$md += ""
$md += "## 💻 CODE"
$md += ""
$md += "**Files:** $($files.Count) | **LOC:** $loc"
$md += ""
foreach ($f in ($files | Sort-Object -Property LOC -Descending | Select-Object -First 10)) {
    $md += "- ``$($f.Path)`` ($($f.LOC) LOC)"
}
$md += ""

# ПРИОРИТЕТЫ
if ($next) {
    $md += "---"
    $md += ""
    $md += "## 🎯 NEXT STEPS"
    $md += ""
    for ($i = 0; $i -lt $next.Count; $i++) {
        $s = $next[$i]
        $pri = if ($s.Priority -le 20) { "🔴 HIGH" } elseif ($s.Priority -le 50) { "🟡 MED" } else { "🟢 LOW" }
        $md += "$($i+1). $pri **$($s.Code)**: $($s.Title)"
    }
    $md += ""
}

$md += "---"
$md += ""
$md += "## 🤖 FOR AI AGENT: UPDATE PROGRESS"
$md += ""
$md += "**After completing a task, run:**"
$md += ""
$md += '```powershell'
$md += "cd $projectRoot\agents\EngineersIT.Bot"
$md += ".\Update-Progress.ps1 -TaskCode 'YOUR-TASK-CODE' -Status 'done'"
$md += '```'
$md += ""
$md += "**Statuses:** done | in_progress | planned | blocked"
$md += ""
$md += "**Example:**"
$md += '```powershell'
$md += ".\Update-Progress.ps1 -TaskCode 'TL-B7-T2' -Status 'done' -Description 'Fixed trades persistence'"
$md += '```'
$md += ""
$md += "---"
$md += ""
$md += "**[OK] Context restored. Ready!**"

$mdText = $md -join "`n"

# СОХРАНИТЬ
$mdText | Out-File -FilePath $sessionFile -Encoding UTF8
Copy-Item -Path $sessionFile -Destination $latestFile -Force

Write-Host "[OK] Saved: $sessionFile" -ForegroundColor Green

# GIT
if (-not $SkipGit) {
    Write-Host "`n[7/7] Git..." -ForegroundColor Yellow
    Push-Location $projectRoot
    try {
        git add $contextDir
        $msg = "feat(context): $Domain @ $timestamp`n`n$pct% ($doneCount/$total) | $($files.Count) files | $loc LOC"
        if ($metrics) { $msg += "`nPnL=$($metrics.PnL)% Sharpe=$($metrics.Sharpe)" }
        git commit -m $msg
        Write-Host "[OK] Committed" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] $_" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
}

# БУФЕР
if (-not $SkipClipboard) {
    Set-Clipboard -Value $mdText
    Write-Host "`n[OK] Clipboard: $($mdText.Length) chars" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan


