# TradLab Scripts

This directory contains scripts for managing TradLab infrastructure and running backtests.

## Quick Start

### 1. Start PostgreSQL

```bash
# Start PostgreSQL container
docker compose -f docker-compose.tradlab.yml up -d

# Check status
docker compose -f docker-compose.tradlab.yml ps
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (optional)
```

### 3. Run Migrations

```bash
# Apply database migrations
python scripts/run_migrations.py
```

### 4. Load Historical Data

```bash
# Load ETH/USDT data from 2024
python scripts/load_data.py --symbol ETH/USDT --start 2024-01-01

# Load specific timeframes
python scripts/load_data.py --symbol ETH/USDT --timeframes 1h,4h --start 2024-01-01
```

### 5. Run Backtest

```bash
# Run STR-100 backtest
python scripts/run_backtest.py --start 2024-01-01 --end 2024-12-31

# With custom capital
python scripts/run_backtest.py --start 2024-01-01 --end 2024-12-31 --capital 50000
```

---

## Scripts Description

### `run_migrations.py`

Executes SQL migrations from `DB/migrations/` folder.

**Features:**
- Connects to PostgreSQL using `DATABASE_URL` from `.env`
- Finds and executes all `.sql` files in order
- Displays progress and errors
- Creates schemas: `market`, `lab`
- Creates tables: `market.ohlcv`, `lab.trades`, `lab.results`, `lab.jobs`

**Usage:**
```bash
python scripts/run_migrations.py
```

---

### `load_data.py`

Loads OHLCV data from Binance using `OHLCVCollector`.

**Arguments:**
| Argument | Default | Description |
|----------|---------|-------------|
| `--symbol` | ETH/USDT | Trading pair |
| `--timeframes` | 1h,4h | Comma-separated timeframes |
| `--start` | 2024-01-01 | Start date (YYYY-MM-DD) |

**Examples:**
```bash
# Load ETH/USDT 1h and 4h data from 2024
python scripts/load_data.py --symbol ETH/USDT --start 2024-01-01

# Load BTC/USDT 1h only from 2023
python scripts/load_data.py --symbol BTC/USDT --timeframes 1h --start 2023-01-01
```

---

### `run_backtest.py`

Runs STR-100 backtest using `BacktesterV1`.

**Arguments:**
| Argument | Default | Description |
|----------|---------|-------------|
| `--symbol` | ETHUSDT | Trading pair |
| `--start` | (required) | Start date (YYYY-MM-DD) |
| `--end` | (required) | End date (YYYY-MM-DD) |
| `--capital` | 10000 | Initial capital (USDT) |

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `TRADLAB_INITIAL_CAPITAL` | 10000 | Default initial capital |
| `TRADLAB_COMMISSION_RATE` | 0.0004 | Commission rate (0.04%) |
| `TRADLAB_SLIPPAGE_BPS` | 5 | Slippage in basis points |

**Output Metrics:**
- **PnL**: Total profit/loss
- **Sharpe Ratio**: Risk-adjusted return
- **Sortino Ratio**: Downside risk-adjusted return
- **Max Drawdown**: Maximum peak-to-trough decline
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / Gross loss
- **Risk Gate**: Pass/Fail based on criteria

**Examples:**
```bash
# Run backtest for 2024
python scripts/run_backtest.py --start 2024-01-01 --end 2024-12-31

# Run with custom capital
python scripts/run_backtest.py --start 2024-01-01 --end 2024-06-30 --capital 50000
```

---

## PostgreSQL Management

### Docker Commands

```bash
# Start PostgreSQL
docker compose -f docker-compose.tradlab.yml up -d

# Stop PostgreSQL
docker compose -f docker-compose.tradlab.yml down

# View logs
docker compose -f docker-compose.tradlab.yml logs -f

# Restart container
docker compose -f docker-compose.tradlab.yml restart

# Remove container and data (CAUTION!)
docker compose -f docker-compose.tradlab.yml down -v
```

### Connect to Database

```bash
# Using psql inside container
docker exec -it tradlab_postgres psql -U tradlab -d tradlab_db

# Using external psql (replace YOUR_PASSWORD_HERE with actual password)
psql postgresql://tradlab:YOUR_PASSWORD_HERE@localhost:5432/tradlab_db
```

---

## SQL Verification Queries

### Check OHLCV Data

```sql
-- Count records by symbol and timeframe
SELECT symbol, tf, COUNT(*) as count,
       MIN(ts) as first_ts, MAX(ts) as last_ts
FROM market.ohlcv
GROUP BY symbol, tf
ORDER BY symbol, tf;

-- Check for gaps in data
SELECT ts, LEAD(ts) OVER (ORDER BY ts) as next_ts,
       LEAD(ts) OVER (ORDER BY ts) - ts as gap
FROM market.ohlcv
WHERE symbol = 'ETHUSDT' AND tf = '4h'
ORDER BY ts;

-- Sample latest data
SELECT * FROM market.ohlcv
WHERE symbol = 'ETHUSDT' AND tf = '4h'
ORDER BY ts DESC
LIMIT 10;
```

### Check Backtest Results

```sql
-- View all backtest runs
SELECT run_id, strategy_id, start_ts, end_ts,
       pnl_total, sharpe, max_dd, win_rate, pass_risk_gate
FROM lab.results
ORDER BY start_ts DESC;

-- View trades for a specific run
SELECT trade_id, side, qty, entry_ts, entry_price,
       exit_ts, exit_price, pnl, pnl_pct
FROM lab.trades
WHERE run_id = 'YOUR_RUN_ID'
ORDER BY entry_ts;

-- Aggregate trade statistics
SELECT 
    COUNT(*) as total_trades,
    COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
    COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    MAX(pnl) as best_trade,
    MIN(pnl) as worst_trade
FROM lab.trades
WHERE run_id = 'YOUR_RUN_ID';
```

### Check Job Status

```sql
-- View recent jobs
SELECT job_id, job_type, status, started_at, finished_at
FROM lab.jobs
ORDER BY started_at DESC
LIMIT 10;
```

---

## Troubleshooting

### Connection Issues

1. **Check if PostgreSQL is running:**
   ```bash
   docker compose -f docker-compose.tradlab.yml ps
   ```

2. **Check PostgreSQL logs:**
   ```bash
   docker compose -f docker-compose.tradlab.yml logs tradlab_postgres
   ```

3. **Verify connection string:**
   ```bash
   cat .env | grep DATABASE_URL
   ```

### Migration Errors

1. **Check if schemas exist:**
   ```sql
   SELECT schema_name FROM information_schema.schemata;
   ```

2. **Re-run migrations (idempotent):**
   ```bash
   python scripts/run_migrations.py
   ```

### Data Loading Issues

1. **Check network connectivity to Binance:**
   ```bash
   curl https://api.binance.com/api/v3/ping
   ```

2. **Verify data in database:**
   ```sql
   SELECT COUNT(*) FROM market.ohlcv;
   ```
