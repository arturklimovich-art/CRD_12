# Configuration Guide

## Overview
This guide explains how to configure the TradLab trading bot system.

## Environment Variables

### Required Variables

```bash
# Binance API Configuration
API_KEY=your_binance_api_key
API_SECRET=your_binance_api_secret
TESTNET=true  # Use 'false' for mainnet (CAUTION!)

# Trading Pair
SYMBOL=ETHUSDT
TIMEFRAME=4h
INITIAL_CAPITAL=10000

# Database Configuration
DB_HOST=localhost
DB_PORT=5434
DB_NAME=tradlab_db
DB_USER=tradlab
DB_PASSWORD=your_password
```

### Strategy Parameters

```bash
# STR-100 Strategy Parameters
MASTER_LONG_THRESHOLD=12.0
MASTER_SHORT_THRESHOLD=-17.0
LOOKBACK_Z=8

# Risk Management
RISK_PER_TRADE=0.01  # 1% per trade
MAX_POSITION_PCT=0.20  # 20% max position size

# Stop Loss / Take Profit
K_SL_MIN=2.2
K_SL_MAX=3.0
K_TP1=2.0
K_TP2=4.0

# Veto Filters
ATR_EXPANSION_MULTIPLIER=2.0
VOLUME_COLLAPSE_MULTIPLIER=0.3

# Trading Costs
COMMISSION_RATE=0.0004  # 0.04%
SLIPPAGE_BPS=5  # 5 basis points
```

### Optional Variables

```bash
# Emergency Settings
EMERGENCY_CLOSE_POSITIONS=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=tradlab.log
```

## Strategy Configuration

### STR-100 ChainFlow ETH

The STR-100 strategy uses the following parameters:

#### Signal Thresholds
- **master_long_threshold**: Threshold for LONG signals (default: 15)
- **master_short_threshold**: Threshold for SHORT signals (default: -15)
- **lookback_z**: Lookback period for Z-score calculation (default: 12)

#### Risk Management
- **risk_per_trade**: Risk per trade as % of capital (0.01 = 1%)
- **max_position_pct**: Maximum position size as % of capital (0.20 = 20%)

#### Stop Loss / Take Profit
- **k_sl_min**: Minimum SL multiplier (1.5)
- **k_sl_max**: Maximum SL multiplier (3.0)
- **k_tp1**: First TP multiplier (2.0)
- **k_tp2**: Second TP multiplier (4.0)
- **k_tsl**: Trailing SL multiplier (1.0)

#### Veto Filters
- **atr_expansion_multiplier**: Reject signals when ATR > ATR_MA * multiplier (2.0)
- **volume_collapse_multiplier**: Reject signals when volume < avg_volume * multiplier (0.3)

#### Exchange Constraints
The strategy respects Binance exchange constraints:

```python
EXCHANGE_CONSTRAINTS = {
    'min_lot_size': 0.001,      # Minimum order size (ETH)
    'max_lot_size': 9000.0,     # Maximum order size (ETH)
    'lot_precision': 3,         # Decimal precision
    'min_notional': 10.0,       # Minimum order value (USDT)
    'tick_size': 0.01          # Price precision
}
```

## Configuration Files

### .env File Structure

Create a `.env` file in the project root:

```bash
# Binance Configuration
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
TESTNET=true

# Trading Configuration
SYMBOL=ETHUSDT
TIMEFRAME=4h
INITIAL_CAPITAL=10000

# Strategy Parameters
MASTER_LONG_THRESHOLD=12.0
MASTER_SHORT_THRESHOLD=-17.0
RISK_PER_TRADE=0.01
MAX_POSITION_PCT=0.20

# Database
DB_HOST=localhost
DB_PORT=5434
DB_NAME=tradlab_db
DB_USER=tradlab
DB_PASSWORD=crd12
```

### Configuration Validation

The bot validates parameters on startup:

```python
def _validate_params(self):
    """Validate strategy parameters"""
    assert 0 < self.params["risk_per_trade"] <= 0.05
    assert 0 < self.params["max_position_pct"] <= 0.50
    assert self.params["k_sl_min"] < self.params["k_sl_max"]
    assert self.params["k_tp1"] < self.params["k_tp2"]
```

## Testnet vs Mainnet

### Testnet Configuration
```bash
TESTNET=true
API_KEY=testnet_api_key
API_SECRET=testnet_api_secret
```

**Testnet characteristics:**
- No real money
- Free test funds
- Same API as mainnet
- Perfect for testing

### Mainnet Configuration
```bash
TESTNET=false
API_KEY=mainnet_api_key
API_SECRET=mainnet_api_secret
```

**⚠️ WARNING:** Mainnet uses real money!
- Start with small amounts
- Test thoroughly on testnet first
- Monitor closely
- Have emergency procedures ready

## Database Configuration

### PostgreSQL Setup

```sql
-- Create database
CREATE DATABASE tradlab_db;

-- Create user
CREATE USER tradlab WITH PASSWORD 'your_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE tradlab_db TO tradlab;
```

### Connection String

```python
db_conn = psycopg2.connect(
    host='localhost',
    port=5434,
    database='tradlab_db',
    user='tradlab',
    password='crd12'
)
```

## Best Practices

### 1. Start Conservative
- Use testnet first
- Start with small risk_per_trade (0.01)
- Limit position size (max_position_pct = 0.20)

### 2. Monitor Performance
- Check logs regularly
- Monitor balance changes
- Review executed trades

### 3. Adjust Parameters Gradually
- Change one parameter at a time
- Test on testnet before mainnet
- Document all changes

### 4. Security
- Never commit `.env` to version control
- Rotate API keys regularly
- Use IP restrictions on Binance API keys

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check API keys are correct
   - Verify TESTNET setting matches your keys
   - Check network connectivity

2. **Invalid Parameters**
   - Review parameter validation rules
   - Check all thresholds are set correctly
   - Ensure numeric values are properly formatted

3. **Order Rejected**
   - Check minimum notional value
   - Verify lot size constraints
   - Review account balance

## Examples

### Conservative Configuration
```bash
RISK_PER_TRADE=0.005  # 0.5%
MAX_POSITION_PCT=0.10  # 10%
MASTER_LONG_THRESHOLD=20.0
MASTER_SHORT_THRESHOLD=-20.0
```

### Aggressive Configuration
```bash
RISK_PER_TRADE=0.02  # 2%
MAX_POSITION_PCT=0.30  # 30%
MASTER_LONG_THRESHOLD=10.0
MASTER_SHORT_THRESHOLD=-10.0
```

## References

- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
