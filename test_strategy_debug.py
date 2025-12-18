import pandas as pd
import numpy as np
from src.tradlab.engine.feature_adapter_v1 import FeatureAdapterV1
from src.tradlab.engine.strategies.str_100_chainflow_eth import STR100ChainFlowETH

# Загружаем фичи
adapter = FeatureAdapterV1("postgresql://tradlab:crd12@localhost:5434/tradlab_db")
df = adapter.fetch_features("ETHUSDT", "2024-03-01", "2024-03-31")
df = adapter.prepare_features_for_strategy(df)

print(f"Загружено {len(df)} баров\n")

# Создаём стратегию
strategy = STR100ChainFlowETH()

# Тестируем на баре 50
if len(df) > 50:
    test_row = df.iloc[50]
    
    print(f"{'='*60}")
    print(f"ТЕСТОВЫЙ БАР: {test_row['ts_4h']}")
    print(f"{'='*60}")
    print(f"Close: {test_row['close_4h']:.2f}")
    print(f"SMA_50: {test_row['sma_50_4h']:.2f}")
    print(f"ATR_14: {test_row['atr_14_1h']:.2f}")
    print(f"Volume: {test_row['volume_4h']:.2f}")
    print(f"Avg Volume 20: {test_row['avg_volume_20']:.2f}")
    
    # Вручную рассчитаем все score'ы
    print(f"\n{'='*60}")
    print(f"РАСЧЁТ SCORE'ОВ")
    print(f"{'='*60}")
    
    # Price Score
    close = test_row['close_4h']
    sma = test_row['sma_50_4h']
    atr = test_row['atr_14_1h']
    distance = (close - sma) / atr
    price_score = np.tanh(distance / 2) * 100
    print(f"Price Score: {price_score:.2f}")
    print(f"  └─ Distance from SMA: {distance:.2f} ATRs")
    
    # Volume Score
    volume = test_row['volume_4h']
    avg_volume = test_row['avg_volume_20']
    volume_ratio = volume / avg_volume
    volume_score = (volume_ratio - 1) * 100
    volume_score = np.clip(volume_score, -100, 100)
    print(f"Volume Score: {volume_score:.2f}")
    print(f"  └─ Volume Ratio: {volume_ratio:.2f}x")
    
    # Sentiment & BTC Corr (placeholders)
    sentiment = 0.0
    btc_corr = 0.0
    print(f"Sentiment: {sentiment:.2f} (placeholder)")
    print(f"BTC Correlation: {btc_corr:.2f} (placeholder)")
    
    # Master Signal
    master = (
        price_score * 0.35 +
        volume_score * 0.30 +
        sentiment * 0.20 +
        btc_corr * 0.15
    )
    print(f"\n{'='*60}")
    print(f"MASTER SIGNAL: {master:.2f}")
    print(f"{'='*60}")
    print(f"  Weights:")
    print(f"    Price:     {price_score * 0.35:.2f} (35%)")
    print(f"    Volume:    {volume_score * 0.30:.2f} (30%)")
    print(f"    Sentiment: {sentiment * 0.20:.2f} (20%)")
    print(f"    BTC Corr:  {btc_corr * 0.15:.2f} (15%)")
    print(f"\n  Thresholds:")
    print(f"    LONG:  > {strategy.params['master_long_threshold']}")
    print(f"    SHORT: < {strategy.params['master_short_threshold']}")
    
    if master > strategy.params['master_long_threshold']:
        print(f"\n  ✅ LONG SIGNAL (master={master:.2f} > {strategy.params['master_long_threshold']})")
    elif master < strategy.params['master_short_threshold']:
        print(f"\n  ✅ SHORT SIGNAL (master={master:.2f} < {strategy.params['master_short_threshold']})")
    else:
        print(f"\n  ❌ NO SIGNAL (master={master:.2f} between thresholds)")
    
    print(f"\n{'='*60}")
    print(f"ГЕНЕРАЦИЯ СИГНАЛА ЧЕРЕЗ СТРАТЕГИЮ")
    print(f"{'='*60}")
    
    # Генерируем сигнал через стратегию
    signal = strategy.generate_signal(test_row, 10000.0)
    
    if signal:
        print(f"✅ СИГНАЛ СГЕНЕРИРОВАН!")
        print(f"   Side: {signal.side}")
        print(f"   Size: {signal.size:.4f} ETH")
        print(f"   Entry: {signal.meta.get('entry_price', 'N/A')}")
        print(f"   SL: {signal.sl:.2f}")
        print(f"   TP1: {signal.tp1:.2f}")
        print(f"   TP2: {signal.tp2:.2f}")
    else:
        print(f"❌ Стратегия не сгенерировала сигнал")
        print(f"   (возможно veto-фильтры заблокировали)")
