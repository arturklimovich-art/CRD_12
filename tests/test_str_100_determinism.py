import pandas as pd
from tradlab.engine.strategies import STR100ChainFlowETH


def test_str100_determinism():
    """Тест детерминизма STR-100"""
    # Фиксированные входные данные
    features = pd.Series({
        "ts_4h": pd.Timestamp("2024-01-01 00:00:00", tz="UTC"),
        "symbol": "ETHUSDT",
        "close_4h": 2100.0,  # Цена выше SMA для позитивного price_score
        "volume_4h": 20000.0,  # Высокий объём для позитивного volume_score
        "sma_50_4h": 1950.0,
        "atr_14_1h": 50.0,
        "avg_volume_20": 12000.0,
        "atr_ma_50_1h": 45.0
    })
    
    account_balance = 10000.0
    
    strategy = STR100ChainFlowETH()
    
    # Генерация сигнала дважды
    signal1 = strategy.generate_signal(features, account_balance)
    signal2 = strategy.generate_signal(features, account_balance)
    
    # Проверка детерминизма
    assert signal1 is not None
    assert signal2 is not None
    
    assert signal1.side == signal2.side
    assert signal1.size == signal2.size
    assert signal1.sl == signal2.sl
    assert signal1.tp1 == signal2.tp1
    assert signal1.tp2 == signal2.tp2
    assert signal1.meta["master_signal"] == signal2.meta["master_signal"]


def test_str100_long_signal():
    """Тест генерации LONG сигнала"""
    features = pd.Series({
        "ts_4h": pd.Timestamp("2024-01-01 00:00:00", tz="UTC"),
        "symbol": "ETHUSDT",
        "close_4h": 2100.0,  # Цена выше SMA
        "volume_4h": 20000.0,  # Высокий объём
        "sma_50_4h": 1950.0,
        "atr_14_1h": 50.0,
        "avg_volume_20": 12000.0,
        "atr_ma_50_1h": 45.0
    })
    
    strategy = STR100ChainFlowETH()
    signal = strategy.generate_signal(features, 10000.0)
    
    assert signal is not None
    assert signal.side == "LONG"
    assert signal.sl < features["close_4h"]
    assert signal.tp1 > features["close_4h"]
    assert signal.tp2 > signal.tp1


def test_str100_veto_filters():
    """Тест Veto-фильтров"""
    # ATR expansion veto
    features = pd.Series({
        "ts_4h": pd.Timestamp("2024-01-01 00:00:00", tz="UTC"),
        "symbol": "ETHUSDT",
        "close_4h": 2100.0,
        "volume_4h": 20000.0,
        "sma_50_4h": 1950.0,
        "atr_14_1h": 150.0,  # Очень высокий ATR
        "avg_volume_20": 12000.0,
        "atr_ma_50_1h": 50.0
    })
    
    strategy = STR100ChainFlowETH()
    signal = strategy.generate_signal(features, 10000.0)
    
    assert signal is None  # Veto должен заблокировать
