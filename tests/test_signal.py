import pytest
from datetime import datetime, timezone
from tradlab.engine import Signal


def test_signal_creation():
    """Тест создания Signal"""
    signal = Signal(
        strategy_id="STR-TEST",
        ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
        symbol="ETHUSDT",
        side="LONG",
        size=1.5,
        sl=1900.0,
        tp1=2100.0,
        tp2=2200.0
    )
    
    assert signal.strategy_id == "STR-TEST"
    assert signal.side == "LONG"
    assert signal.size == 1.5


def test_signal_invalid_side():
    """Тест валидации side"""
    with pytest.raises(ValueError):
        Signal(
            strategy_id="STR-TEST",
            ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
            symbol="ETHUSDT",
            side="INVALID",
            size=1.0,
            sl=1900.0,
            tp1=2100.0,
            tp2=2200.0
        )


def test_signal_to_dict():
    """Тест преобразования в dict"""
    signal = Signal(
        strategy_id="STR-TEST",
        ts=datetime(2024, 1, 1, tzinfo=timezone.utc),
        symbol="ETHUSDT",
        side="LONG",
        size=1.5,
        sl=1900.0,
        tp1=2100.0,
        tp2=2200.0
    )
    
    data = signal.to_dict()
    assert data["strategy_id"] == "STR-TEST"
    assert data["side"] == "LONG"
