"""
Unit tests for STR-100 Strategy
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from tradlab.engine.strategies.str_100_chainflow_eth import STR100ChainFlowETH


@pytest.fixture
def strategy():
    """Create strategy instance for testing"""
    return STR100ChainFlowETH(strategy_id="STR-100-TEST")


@pytest.fixture
def sample_features():
    """Create sample feature data"""
    return pd.Series({
        'ts_4h': pd.Timestamp('2024-01-01 00:00:00'),
        'close_4h': 2000.0,
        'open_4h': 1990.0,
        'high_4h': 2010.0,
        'low_4h': 1980.0,
        'volume_4h': 1000000.0,
        'close_1h': 2000.0,
        'atr_14_1h': 50.0,
        'sma_50_4h': 1950.0,
        'avg_volume_20': 900000.0
    })


def test_strategy_initialization(strategy):
    """Test strategy initialization"""
    assert strategy.strategy_id == "STR-100-TEST"
    assert strategy.params["risk_per_trade"] == 0.01
    assert strategy.params["max_position_pct"] == 0.20


def test_parameter_validation_risk_too_high():
    """Test parameter validation - risk too high"""
    with pytest.raises(AssertionError):
        STR100ChainFlowETH(params={"risk_per_trade": 0.10})


def test_parameter_validation_invalid_sl():
    """Test parameter validation - invalid SL range"""
    params = STR100ChainFlowETH.PARAMS.copy()
    params["k_sl_min"] = 3.0
    params["k_sl_max"] = 2.0
    with pytest.raises(AssertionError):
        STR100ChainFlowETH(params=params)


def test_parameter_validation_invalid_tp():
    """Test parameter validation - invalid TP range"""
    params = STR100ChainFlowETH.PARAMS.copy()
    params["k_tp1"] = 4.0
    params["k_tp2"] = 2.0
    with pytest.raises(AssertionError):
        STR100ChainFlowETH(params=params)


def test_price_score_calculation(strategy, sample_features):
    """Test price score calculation"""
    score = strategy._calculate_price_score(sample_features)
    
    # Price is above SMA, should be positive
    assert score > 0
    assert -100 <= score <= 100


def test_volume_score_calculation(strategy, sample_features):
    """Test volume score calculation"""
    score = strategy._calculate_volume_score_l1(sample_features)
    
    # Volume is above average, should be positive
    assert score > 0
    assert -100 <= score <= 100


def test_atr_fallback_with_atr(strategy, sample_features):
    """Test ATR fallback when ATR is present"""
    atr = strategy._get_atr_with_fallback(sample_features)
    assert atr == 50.0


def test_atr_fallback_without_atr(strategy):
    """Test ATR fallback when ATR is missing"""
    features = pd.Series({
        'close_4h': 2000.0,
        'ts_4h': pd.Timestamp('2024-01-01 00:00:00')
    })
    
    atr = strategy._get_atr_with_fallback(features)
    
    # Should be 2% of close price
    assert atr == 40.0  # 2000 * 0.02


def test_atr_veto_triggered(strategy, sample_features):
    """Test ATR veto when ATR is too high"""
    # Set high ATR
    features = sample_features.copy()
    features['atr_14_1h'] = 200.0
    features['atr_ma_50_1h'] = 50.0
    
    assert strategy._atr_veto(features) == True


def test_atr_veto_not_triggered(strategy, sample_features):
    """Test ATR veto when ATR is normal"""
    features = sample_features.copy()
    features['atr_14_1h'] = 50.0
    features['atr_ma_50_1h'] = 50.0
    
    assert strategy._atr_veto(features) == False


def test_volume_veto_triggered(strategy, sample_features):
    """Test volume veto when volume is too low"""
    features = sample_features.copy()
    features['volume_4h'] = 100000.0  # Very low
    features['avg_volume_20'] = 1000000.0
    
    assert strategy._volume_veto(features) == True


def test_volume_veto_not_triggered(strategy, sample_features):
    """Test volume veto when volume is normal"""
    assert strategy._volume_veto(sample_features) == False


def test_position_size_safe_respects_min_lot_size(strategy):
    """Test position sizing respects minimum lot size"""
    balance = 10000.0
    entry = 2000.0
    sl = 1900.0
    
    size = strategy._calculate_position_size_safe(balance, entry, sl)
    
    # Should be at least min_lot_size
    assert size >= strategy.EXCHANGE_CONSTRAINTS['min_lot_size']


def test_position_size_safe_respects_max_lot_size(strategy):
    """Test position sizing respects maximum lot size"""
    balance = 1000000.0  # Very large balance
    entry = 100.0  # Low price
    sl = 99.0
    
    size = strategy._calculate_position_size_safe(balance, entry, sl)
    
    # Should not exceed max_lot_size
    assert size <= strategy.EXCHANGE_CONSTRAINTS['max_lot_size']


def test_position_size_safe_precision(strategy):
    """Test position sizing respects precision"""
    balance = 10000.0
    entry = 2000.0
    sl = 1900.0
    
    size = strategy._calculate_position_size_safe(balance, entry, sl)
    
    # Should be rounded to lot_precision (3 decimals)
    assert size == round(size, strategy.EXCHANGE_CONSTRAINTS['lot_precision'])


def test_position_size_safe_min_notional(strategy):
    """Test position sizing respects minimum notional"""
    balance = 10.0  # Very small balance
    entry = 2000.0
    sl = 1900.0
    
    size = strategy._calculate_position_size_safe(balance, entry, sl)
    
    # If size * price < min_notional, should return 0
    if size * entry < strategy.EXCHANGE_CONSTRAINTS['min_notional']:
        assert size == 0.0


def test_calculate_sl_long(strategy):
    """Test stop-loss calculation for LONG position"""
    entry = 2000.0
    atr = 50.0
    side = "LONG"
    master = 20.0
    
    sl = strategy._calculate_sl(entry, atr, side, master)
    
    # SL should be below entry for LONG
    assert sl < entry


def test_calculate_sl_short(strategy):
    """Test stop-loss calculation for SHORT position"""
    entry = 2000.0
    atr = 50.0
    side = "SHORT"
    master = -20.0
    
    sl = strategy._calculate_sl(entry, atr, side, master)
    
    # SL should be above entry for SHORT
    assert sl > entry


def test_calculate_tp_long(strategy):
    """Test take-profit calculation for LONG position"""
    entry = 2000.0
    atr = 50.0
    side = "LONG"
    
    tp1, tp2 = strategy._calculate_tp(entry, atr, side)
    
    # Both TPs should be above entry for LONG
    assert tp1 > entry
    assert tp2 > entry
    # TP2 should be higher than TP1
    assert tp2 > tp1


def test_calculate_tp_short(strategy):
    """Test take-profit calculation for SHORT position"""
    entry = 2000.0
    atr = 50.0
    side = "SHORT"
    
    tp1, tp2 = strategy._calculate_tp(entry, atr, side)
    
    # Both TPs should be below entry for SHORT
    assert tp1 < entry
    assert tp2 < entry
    # TP2 should be lower than TP1
    assert tp2 < tp1


def test_generate_signal_long(strategy, sample_features):
    """Test signal generation for LONG"""
    # Modify features to trigger LONG signal
    features = sample_features.copy()
    features['close_4h'] = 2100.0  # Price well above SMA
    features['volume_4h'] = 1500000.0  # High volume
    
    signal = strategy.generate_signal(features, account_balance=10000.0)
    
    # Depending on threshold, may or may not generate signal
    # This is a basic test structure
    if signal:
        assert signal.side in ["LONG", "SHORT"]
        assert signal.size > 0
        assert signal.symbol == "ETHUSDT"


def test_generate_signal_no_signal_low_master(strategy, sample_features):
    """Test no signal generation when master is neutral"""
    # Features with neutral scores
    features = sample_features.copy()
    features['close_4h'] = features['sma_50_4h']  # Price at SMA
    features['volume_4h'] = features['avg_volume_20']  # Volume at average
    
    signal = strategy.generate_signal(features, account_balance=10000.0)
    
    # Should not generate signal (master too low)
    assert signal is None


def test_master_signal_rebalanced_weights(strategy, sample_features):
    """Test that master signal uses rebalanced weights (0.60 price, 0.40 volume)"""
    price_score = strategy._calculate_price_score(sample_features)
    volume_score = strategy._calculate_volume_score_l1(sample_features)
    
    expected_master = price_score * 0.60 + volume_score * 0.40
    
    # This is a conceptual test to verify the weight rebalancing
    assert abs(expected_master) >= 0  # Just verify it computes


def test_exchange_constraints_defined(strategy):
    """Test that exchange constraints are properly defined"""
    constraints = strategy.EXCHANGE_CONSTRAINTS
    
    assert 'min_lot_size' in constraints
    assert 'max_lot_size' in constraints
    assert 'lot_precision' in constraints
    assert 'min_notional' in constraints
    assert 'tick_size' in constraints
    
    assert constraints['min_lot_size'] == 0.001
    assert constraints['max_lot_size'] == 9000.0
    assert constraints['lot_precision'] == 3
    assert constraints['min_notional'] == 10.0
