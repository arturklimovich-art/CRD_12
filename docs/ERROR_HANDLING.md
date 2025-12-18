# Error Handling Patterns

## Overview
This document describes error handling patterns used in the TradLab trading bot system.

## Exception Hierarchy

### API Exceptions

#### Binance API Errors
Common Binance API error codes and handling:

```python
try:
    order = self.exchange.place_market_order(...)
except BinanceAPIException as e:
    if e.code == -1021:
        # Timestamp error - retry with time sync
        self._sync_time()
        return self.execute_trade(signal)
    
    elif e.code in [-2010, -1013]:
        # Balance/quantity issues
        logger.critical(f"Order rejected: {e.message}")
        self._send_alert(f"ORDER_REJECTED: {e.message}")
    
    elif e.code == -1003:
        # Rate limit exceeded
        logger.warning("Rate limit exceeded, waiting...")
        time.sleep(60)
    
    else:
        # Unknown API error
        logger.critical(f"Unhandled API error: {e.code}")
        self._emergency_shutdown()
```

### Network Exceptions

#### Timeout Handling
```python
for attempt in range(max_retries):
    try:
        result = api_call()
        break
    except Timeout:
        if attempt < max_retries - 1:
            wait_time = retry_delay * (attempt + 1)
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
            time.sleep(wait_time)
        else:
            logger.error("Max retries exceeded")
            raise
```

#### Network Errors
```python
try:
    response = api_call()
except NetworkError as e:
    logger.error(f"Network error: {e}")
    # Implement wait and retry logic
    self._wait_and_retry(signal)
```

## Error Handling Patterns

### 1. Try-Except-Finally Pattern

```python
def execute_trade(self, signal):
    """Execute trade with comprehensive error handling"""
    try:
        # Pre-validation
        if not self._validate_signal(signal):
            return None
        
        # Execute order
        order = self.connector.create_order(...)
        logger.info(f"✅ Order executed: {order['orderId']}")
        return order
    
    except BinanceAPIException as e:
        # Handle API-specific errors
        self._handle_api_error(e, signal)
        return None
    
    except NetworkError as e:
        # Handle network errors
        logger.error(f"Network error: {e}")
        return None
    
    except Exception as e:
        # Catch-all for unexpected errors
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        self._emergency_shutdown()
        return None
    
    finally:
        # Cleanup code (if needed)
        pass
```

### 2. Validation Pattern

```python
def _validate_signal(self, signal) -> bool:
    """Validate signal before execution"""
    if not signal:
        logger.error("Signal is None")
        return False
    
    required_attrs = ['side', 'position_size', 'entry_price', 'stop_loss']
    for attr in required_attrs:
        if not hasattr(signal, attr):
            logger.error(f"Signal missing required attribute: {attr}")
            return False
    
    if signal.position_size <= 0:
        logger.error(f"Invalid position size: {signal.position_size}")
        return False
    
    return True
```

### 3. Feature Validation Pattern

```python
def get_features(self, ts: pd.Timestamp) -> Optional[pd.Series]:
    """Get features with validation"""
    try:
        features = df.loc[ts]
        
        # Validate required features
        required = ["close_4h", "volume_4h", "ts_4h"]
        missing = [f for f in required if f not in features or pd.isna(features[f])]
        
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        return features
        
    except KeyError:
        logger.error(f"No features for timestamp {ts}")
        return None
    except Exception as e:
        logger.error(f"Feature error: {e}")
        return None
```

### 4. Retry with Exponential Backoff

```python
def api_call_with_retry(self, func, *args, **kwargs):
    """Execute API call with exponential backoff retry"""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Timeout:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
                time.sleep(delay)
            else:
                logger.error("Max retries exceeded")
                raise
        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1}: {e}")
            raise
```

## Emergency Procedures

### 1. Emergency Shutdown

```python
def _emergency_shutdown(self):
    """Emergency shutdown procedure"""
    logger.critical("🚨 EMERGENCY SHUTDOWN")
    
    # Close positions if configured
    if self.config.get('EMERGENCY_CLOSE_POSITIONS', True):
        try:
            self._close_all_positions()
        except Exception as e:
            logger.error(f"Failed to close positions: {e}")
    
    # Send alert
    self._send_alert("EMERGENCY_SHUTDOWN")
    
    # Stop bot
    self.running = False
    sys.exit(1)
```

### 2. Position Cleanup

```python
def _close_all_positions(self):
    """Close all open positions"""
    if not self.current_position:
        return
    
    try:
        logger.warning("Closing all positions...")
        self.close_position("EMERGENCY", partial=1.0)
        logger.info("All positions closed")
    except Exception as e:
        logger.error(f"Error closing positions: {e}")
        raise
```

## Alert System

### 1. Alert Levels

```python
ALERT_LEVELS = {
    'INFO': 0,
    'WARNING': 1,
    'ERROR': 2,
    'CRITICAL': 3
}

def _send_alert(self, message: str, level: str = 'WARNING'):
    """Send alert through configured channels"""
    logger.log(ALERT_LEVELS[level], f"🚨 ALERT: {message}")
    
    # Send to Telegram (if configured)
    if self.telegram_bot:
        self.telegram_bot.send_message(message)
    
    # Send to email (if configured)
    if self.email_alerts:
        self.email_sender.send(message)
```

### 2. Alert Scenarios

```python
# Order Rejected
self._send_alert(f"ORDER_REJECTED: {error_message}", level='ERROR')

# Emergency Shutdown
self._send_alert("EMERGENCY_SHUTDOWN", level='CRITICAL')

# Network Issues
self._send_alert("NETWORK_ISSUES: Retrying...", level='WARNING')

# Position Closed
self._send_alert(f"POSITION_CLOSED: {reason}", level='INFO')
```

## Logging Best Practices

### 1. Log Levels

```python
# DEBUG: Detailed information for debugging
logger.debug(f"Signal details: {signal.to_dict()}")

# INFO: General informational messages
logger.info(f"✅ Order executed: {order_id}")

# WARNING: Warning messages for potentially harmful situations
logger.warning(f"⚠️ ATR missing, using fallback")

# ERROR: Error messages for recoverable errors
logger.error(f"❌ API error: {error_code}")

# CRITICAL: Critical messages for non-recoverable errors
logger.critical(f"🚨 EMERGENCY SHUTDOWN")
```

### 2. Structured Logging

```python
logger.info(f"Order executed", extra={
    'order_id': order['orderId'],
    'side': signal.side,
    'quantity': quantity,
    'price': price,
    'timestamp': datetime.now().isoformat()
})
```

### 3. Sensitive Data Protection

```python
# ❌ WRONG - Exposes API key
logger.info(f"Config: {self.config}")

# ✅ CORRECT - Sanitized logging
logger.info(f"Config loaded: {self.safe_config}")
```

## Error Recovery Strategies

### 1. Automatic Recovery

```python
def _auto_recover(self, error_type: str):
    """Attempt automatic recovery from known errors"""
    
    if error_type == 'TIMESTAMP_ERROR':
        self._sync_time()
        return True
    
    elif error_type == 'RATE_LIMIT':
        time.sleep(60)
        return True
    
    elif error_type == 'NETWORK_ERROR':
        time.sleep(10)
        return True
    
    return False
```

### 2. Manual Intervention Required

```python
MANUAL_INTERVENTION_CODES = [-2010, -1013, -2011]

def requires_manual_intervention(error_code: int) -> bool:
    """Check if error requires manual intervention"""
    return error_code in MANUAL_INTERVENTION_CODES
```

## Testing Error Scenarios

### 1. Unit Tests for Error Handling

```python
def test_invalid_signal():
    """Test handling of invalid signals"""
    bot = LiveTradingBot()
    
    # Test None signal
    result = bot.execute_trade(None)
    assert result is None
    
    # Test missing attributes
    signal = Signal(side='LONG', size=0)
    result = bot.execute_trade(signal)
    assert result is None
```

### 2. Integration Tests

```python
def test_network_timeout():
    """Test handling of network timeouts"""
    with patch('binance.client.Client.create_order', side_effect=Timeout):
        bot = LiveTradingBot()
        result = bot.execute_trade(valid_signal)
        assert result is None
```

## Monitoring and Observability

### 1. Error Metrics

Track the following metrics:
- Error rate by type
- Recovery success rate
- Emergency shutdown frequency
- API timeout frequency

### 2. Error Dashboard

Monitor in real-time:
- Recent errors (last 24h)
- Error trends
- Alert status
- Recovery actions taken

## Best Practices Summary

1. **Always validate inputs** before processing
2. **Use specific exception types** instead of bare except
3. **Log errors with context** (timestamps, relevant data)
4. **Implement retry logic** for transient failures
5. **Have emergency procedures** for critical failures
6. **Send alerts** for important events
7. **Never expose sensitive data** in logs or errors
8. **Test error scenarios** thoroughly
9. **Monitor error rates** in production
10. **Document recovery procedures** for common errors

## References

- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
- [Binance API Error Codes](https://binance-docs.github.io/apidocs/spot/en/#error-codes)
- [Logging Best Practices](https://docs.python.org/3/howto/logging.html)
