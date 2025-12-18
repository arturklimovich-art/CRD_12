"""
Unit tests for Position Sizing
"""
import pytest
from tradlab.engine.strategies.str_100_chainflow_eth import STR100ChainFlowETH


@pytest.fixture
def strategy():
    """Create strategy instance for testing"""
    return STR100ChainFlowETH(strategy_id="STR-100-TEST")


class TestPositionSizing:
    """Test position sizing functionality"""
    
    def test_basic_position_sizing(self, strategy):
        """Test basic position sizing calculation"""
        balance = 10000.0
        entry = 2000.0
        sl = 1900.0  # 5% stop loss
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Verify size is calculated
        assert size > 0
        
        # Verify position doesn't risk more than configured
        max_loss = balance * strategy.params["risk_per_trade"]
        actual_loss = size * entry * abs(entry - sl) / entry
        assert actual_loss <= max_loss * 1.01  # Allow 1% margin for rounding
    
    def test_min_lot_size_constraint(self, strategy):
        """Test minimum lot size constraint"""
        balance = 1.0  # Very small balance
        entry = 2000.0
        sl = 1950.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should either be 0 (below min notional) or >= min_lot_size
        if size > 0:
            assert size >= strategy.EXCHANGE_CONSTRAINTS['min_lot_size']
    
    def test_max_lot_size_constraint(self, strategy):
        """Test maximum lot size constraint"""
        balance = 10000000.0  # Very large balance
        entry = 100.0  # Low price
        sl = 99.5
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should not exceed max_lot_size
        assert size <= strategy.EXCHANGE_CONSTRAINTS['max_lot_size']
    
    def test_lot_precision_constraint(self, strategy):
        """Test lot precision constraint"""
        balance = 10000.0
        entry = 2000.0
        sl = 1900.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should be rounded to lot_precision decimals
        precision = strategy.EXCHANGE_CONSTRAINTS['lot_precision']
        assert size == round(size, precision)
    
    def test_min_notional_constraint(self, strategy):
        """Test minimum notional value constraint"""
        balance = 5.0  # Small balance
        entry = 2000.0
        sl = 1900.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # If size * entry < min_notional, size should be 0
        min_notional = strategy.EXCHANGE_CONSTRAINTS['min_notional']
        if size * entry < min_notional:
            assert size == 0.0
        else:
            assert size * entry >= min_notional
    
    def test_max_position_percentage(self, strategy):
        """Test maximum position percentage constraint"""
        balance = 10000.0
        entry = 2000.0
        sl = 1999.0  # Very tight stop loss
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Position value should not exceed max_position_pct of balance
        max_position_value = balance * strategy.params["max_position_pct"]
        actual_position_value = size * entry
        assert actual_position_value <= max_position_value * 1.01  # Allow 1% margin
    
    def test_risk_per_trade_respected(self, strategy):
        """Test that risk per trade is respected"""
        balance = 10000.0
        entry = 2000.0
        sl = 1900.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Calculate actual risk
        distance_to_sl = abs(entry - sl) / entry
        max_loss = size * entry * distance_to_sl
        
        # Should not exceed risk_per_trade of balance
        max_risk = balance * strategy.params["risk_per_trade"]
        assert max_loss <= max_risk * 1.01  # Allow 1% margin for rounding
    
    def test_zero_size_when_below_min_notional(self, strategy):
        """Test that size is 0 when notional value is too small"""
        balance = 1.0
        entry = 2000.0
        sl = 1950.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        if size * entry < strategy.EXCHANGE_CONSTRAINTS['min_notional']:
            assert size == 0.0
    
    def test_position_sizing_with_different_risks(self, strategy):
        """Test position sizing with different risk parameters"""
        balance = 10000.0
        entry = 2000.0
        
        # Test with tight stop loss (5% away)
        sl_tight = 1900.0
        size_tight = strategy._calculate_position_size_safe(balance, entry, sl_tight)
        
        # Test with wide stop loss (10% away)
        sl_wide = 1800.0
        size_wide = strategy._calculate_position_size_safe(balance, entry, sl_wide)
        
        # Tighter stop loss should allow larger position size (for same risk)
        assert size_tight > size_wide
    
    def test_position_sizing_consistency(self, strategy):
        """Test that position sizing is consistent"""
        balance = 10000.0
        entry = 2000.0
        sl = 1900.0
        
        size1 = strategy._calculate_position_size_safe(balance, entry, sl)
        size2 = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should return same size for same inputs
        assert size1 == size2


class TestPositionSizingEdgeCases:
    """Test edge cases in position sizing"""
    
    def test_zero_balance(self, strategy):
        """Test with zero balance"""
        balance = 0.0
        entry = 2000.0
        sl = 1900.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should return 0 or very small size
        assert size == 0.0
    
    def test_negative_balance(self, strategy):
        """Test with negative balance (should not happen but test defensive code)"""
        balance = -1000.0
        entry = 2000.0
        sl = 1900.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should handle gracefully (return 0 or raise error)
        assert size >= 0.0
    
    def test_sl_equals_entry(self, strategy):
        """Test with stop loss equal to entry"""
        balance = 10000.0
        entry = 2000.0
        sl = 2000.0  # Same as entry
        
        # This should either return 0 or handle the division carefully
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Since there's no risk, size could be very large or 0
        # Just verify it doesn't crash
        assert size >= 0.0
    
    def test_very_small_price(self, strategy):
        """Test with very small price"""
        balance = 10000.0
        entry = 0.01
        sl = 0.009
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should handle small prices correctly
        assert size >= 0.0
    
    def test_very_large_price(self, strategy):
        """Test with very large price"""
        balance = 10000.0
        entry = 100000.0
        sl = 99000.0
        
        size = strategy._calculate_position_size_safe(balance, entry, sl)
        
        # Should handle large prices correctly
        assert size >= 0.0
        
        # Size should be very small due to high price
        assert size * entry <= balance * strategy.params["max_position_pct"]


class TestOldPositionSizing:
    """Test the old position sizing method for comparison"""
    
    def test_old_vs_new_position_sizing(self, strategy):
        """Compare old and new position sizing methods"""
        balance = 10000.0
        entry = 2000.0
        sl = 1900.0
        
        size_new = strategy._calculate_position_size_safe(balance, entry, sl)
        size_old = strategy._calculate_position_size(balance, entry, sl)
        
        # New method should apply constraints
        # Old method might not
        # Verify new method size is valid
        assert size_new >= 0.0
        
        # If old method returns larger size, new method should constrain it
        if size_old > strategy.EXCHANGE_CONSTRAINTS['max_lot_size']:
            assert size_new <= strategy.EXCHANGE_CONSTRAINTS['max_lot_size']
