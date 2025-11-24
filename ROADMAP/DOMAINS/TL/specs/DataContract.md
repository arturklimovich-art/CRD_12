# 📊 DATA CONTRACT — TradLab

## 🗄️ Схема: market

### Таблица: market.ohlcv
Хранение OHLCV данных с бирж.

**Структура:**
```sql
CREATE TABLE market.ohlcv (
  id      BIGSERIAL PRIMARY KEY,
  symbol  TEXT NOT NULL,           -- "ETHUSDT"
  tf      TEXT NOT NULL,           -- "1h", "4h"
  ts      TIMESTAMPTZ NOT NULL,    -- UTC timestamp
  open    DOUBLE PRECISION NOT NULL,
  high    DOUBLE PRECISION NOT NULL,
  low     DOUBLE PRECISION NOT NULL,
  close   DOUBLE PRECISION NOT NULL,
  volume  DOUBLE PRECISION NOT NULL,
  source  TEXT NOT NULL,           -- "binance"
  UNIQUE (symbol, tf, ts)
);

CREATE INDEX idx_ohlcv_symbol_tf_ts
  ON market.ohlcv(symbol, tf, ts);
```

**Пример данных:**
| symbol | tf | ts | open | high | low | close | volume | source |
|--------|----|----|------|------|-----|-------|--------|--------|
| ETHUSDT | 4h | 2024-01-01 00:00:00+00 | 2250.50 | 2280.30 | 2240.10 | 2275.80 | 15420.5 | binance |

---

## 🗄️ Схема: lab

### Таблица: lab.trades
Хранение всех сделок (backtest + demo).

**Структура:**
```sql
CREATE TABLE lab.trades (
  trade_id    BIGSERIAL PRIMARY KEY,
  run_id      TEXT NOT NULL,
  strategy_id TEXT NOT NULL,       -- "STR-100"
  mode        TEXT NOT NULL,       -- "backtest" | "demo"
  symbol      TEXT NOT NULL,
  side        TEXT NOT NULL,       -- "LONG" | "SHORT"
  qty         DOUBLE PRECISION NOT NULL,
  entry_ts    TIMESTAMPTZ NOT NULL,
  entry_price DOUBLE PRECISION NOT NULL,
  exit_ts     TIMESTAMPTZ,
  exit_price  DOUBLE PRECISION,
  pnl         DOUBLE PRECISION,
  pnl_pct     DOUBLE PRECISION,
  meta        JSONB
);
```

**Пример данных:**
| trade_id | run_id | strategy_id | mode | symbol | side | qty | entry_ts | entry_price | exit_ts | exit_price | pnl | pnl_pct |
|----------|--------|-------------|------|--------|------|-----|----------|-------------|---------|------------|-----|---------|
| 1 | STR-100_20240101 | STR-100 | backtest | ETHUSDT | LONG | 1.5 | 2024-01-05 08:00 | 2250.50 | 2024-01-08 12:00 | 2350.20 | 149.55 | 4.43 |

---

### Таблица: lab.results
Агрегированные результаты бэктестов.

**Структура:**
```sql
CREATE TABLE lab.results (
  run_id         TEXT PRIMARY KEY,
  strategy_id    TEXT NOT NULL,
  start_ts       TIMESTAMPTZ NOT NULL,
  end_ts         TIMESTAMPTZ NOT NULL,
  pnl_total      DOUBLE PRECISION NOT NULL,
  sharpe         DOUBLE PRECISION,
  sortino        DOUBLE PRECISION,
  max_dd         DOUBLE PRECISION,
  calmar         DOUBLE PRECISION,
  win_rate       DOUBLE PRECISION,
  profit_factor  DOUBLE PRECISION,
  pass_risk_gate BOOLEAN,
  meta           JSONB
);
```

---

### Таблица: lab.jobs
Статусы задач TradLab.

**Структура:**
```sql
CREATE TABLE lab.jobs (
  job_id      BIGSERIAL PRIMARY KEY,
  job_type    TEXT NOT NULL,  -- "collect","backtest","risk","report","demo_run"
  status      TEXT NOT NULL,  -- "pending","running","done","error"
  started_at  TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  meta        JSONB
);
```

---

### View: lab.features_v1
Объединённые фичи для стратегий.

**Структура:**
```sql
CREATE OR REPLACE VIEW lab.features_v1 AS
SELECT
  o4h.symbol,
  o4h.ts           AS ts_4h,
  o4h.open         AS open_4h,
  o4h.high         AS high_4h,
  o4h.low          AS low_4h,
  o4h.close        AS close_4h,
  o4h.volume       AS volume_4h,
  o1h.close        AS close_1h,
  NULL::DOUBLE PRECISION AS atr_14_1h,
  NULL::DOUBLE PRECISION AS sma_50_4h
FROM market.ohlcv o4h
LEFT JOIN market.ohlcv o1h
  ON o1h.symbol = o4h.symbol AND o1h.tf = '1h' AND o1h.ts = o4h.ts
WHERE o4h.tf = '4h';
```

---

## ⏰ Временные зоны
**Все timestamps хранятся в UTC.**

## 📅 Версия контракта
- **Версия:** 1.0.0
- **Дата:** 2025-11-24
- **Автор:** arturklimovich-art