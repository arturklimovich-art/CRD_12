# 📊 REPORT CONTRACT — TradLab

## 📁 Структура отчётов

### Путь к отчётам
```
/app/workspace/reports/TL/{strategy_id}/run_{run_id}/
```

**Пример:**
```
/app/workspace/reports/TL/STR-100/run_20251124_150700/
├── metrics.json
├── trades.csv
├── equity_curve.png (опционально для L1)
└── summary.md
```

---

## 📄 metrics.json

**Структура:**
```json
{
  "run_id": "STR-100_20251124_150700",
  "strategy_id": "STR-100",
  "symbol": "ETHUSDT",
  "mode": "backtest",
  "start_ts": "2019-01-01T00:00:00Z",
  "end_ts": "2024-12-31T23:59:59Z",
  "metrics": {
    "pnl_total": 1523.40,
    "pnl_total_pct": 15.23,
    "sharpe": 1.45,
    "sortino": 1.89,
    "max_dd": -12.3,
    "max_dd_pct": -12.3,
    "calmar": 1.23,
    "win_rate": 58.3,
    "profit_factor": 1.67,
    "total_trades": 342,
    "avg_trade_pnl": 4.45,
    "avg_win": 28.30,
    "avg_loss": -17.20
  },
  "risk_gate": {
    "pass": true,
    "min_trades": 200,
    "actual_trades": 342,
    "dsr": 0.23,
    "dsr_threshold": 0.1,
    "pbo": 0.34,
    "pbo_threshold": 0.5
  },
  "generated_at": "2025-11-24T15:07:00Z"
}
```

---

## 📄 trades.csv

**Структура:**
```csv
trade_id,run_id,strategy_id,mode,symbol,side,qty,entry_ts,entry_price,exit_ts,exit_price,pnl,pnl_pct
1,STR-100_20251124_150700,STR-100,backtest,ETHUSDT,LONG,1.5,2019-01-05T08:00:00Z,150.23,2019-01-08T12:00:00Z,162.45,18.33,8.13
2,STR-100_20251124_150700,STR-100,backtest,ETHUSDT,SHORT,2.0,2019-01-10T16:00:00Z,165.80,2019-01-12T04:00:00Z,158.20,15.20,4.58
```

---

## 📄 summary.md

**Шаблон:**
```markdown
# Backtest Report: {strategy_id}

**Run ID:** {run_id}
**Period:** {start_ts} to {end_ts}
**Symbol:** {symbol}
**Initial Capital:** ${initial_capital}

## Metrics
- **Total PnL:** ${pnl_total} (+{pnl_total_pct}%)
- **Sharpe Ratio:** {sharpe}
- **Sortino Ratio:** {sortino}
- **Max Drawdown:** {max_dd}%
- **Calmar Ratio:** {calmar}
- **Win Rate:** {win_rate}%
- **Profit Factor:** {profit_factor}
- **Total Trades:** {total_trades}

## Risk-Gate Result
{pass ? "✅ PASSED" : "❌ FAILED"}

- Min Trades: {min_trades} (actual: {actual_trades})
- DSR: {dsr} (threshold: {dsr_threshold})
- PBO: {pbo} (threshold: {pbo_threshold})

## Recommendation
{recommendation_text}
```

---

## 📅 Версия контракта
- **Версия:** 1.0.0
- **Дата:** 2025-11-24
- **Автор:** arturklimovich-art