🎯 STR-100: ChainFlow Alpha v3.2 (только ETH)
📋 СПЕЦИФИКАЦИЯ СТРАТЕГИИ (100% ДЕТЕРМИНИРОВАННАЯ)
Основные параметры
strategy_id: STR-100
символ: ETHUSDT
timeframe_main: 4H
timeframe_fast: 1H
тип: Гибридная система, управляемая событиями
1️⃣ MASTER_SIGNAL (основной триггер)
Формула:
MASTER_SIGNAL = (Price_Score × 0.35) + (Volume_Score × 0.30) + (Sentiment × 0.20) + (BTC_Correlation × 0.15)
Диапазон: от -100 до +100
Интерпретация:
if MASTER_SIGNAL_ADJUSTED > 40:
    signal = "LONG"
elif MASTER_SIGNAL_ADJUSTED < -40:
    signal = "SHORT"
else:
    signal = None  # Нейтральная зона (без входа)
2️⃣ SCORE'Ы (компоненты MASTER_SIGNAL)
2,1. Price_Score (35%)
def calculate_price_score(close_4h, sma_50_4h, atr_14_1h):
    """
    Измеряет расстояние цены от SMA(50) в единицах ATR
    
    Вход:
        close_4h: цена закрытия 4H-бара
        sma_50_4h: простая скользящая средняя (50 периодов, 4H)
        atr_14_1h: Average True Range (14 периодов, 1H)
    
    Выход:
        score: от -100 до +100
    """
    distance = (close_4h - sma_50_4h) / atr_14_1h
    score = np.tanh(distance / 2) * 100  # Нормализация в -100..+100
    return score
Интерпретация:

score > 0 → цена выше SMA (бычий)
score < 0 → цена ниже SMA (медвежье)
score ≈ 0 → цена около SMA (нейтрально)
2,2. Volume_Score (30%)
def calculate_volume_score(volume_4h, avg_volume_20, cex_netflow_1h, whale_inflow_4h):
    """
    Комбинированная оценка объёмов (биржа + on-chain)
    
    Вход:
        volume_4h: объём торгов на 4H-баре
        avg_volume_20: средний объём за последние 20 баров (4H)
        cex_netflow_1h: чистый приток на централизованные биржи (1H, ETH)
        whale_inflow_4h: приток от китов (адреса >1000 ETH, 4H)
    
    Выход:
        score: от -100 до +100
    """
    # Компонент 1: Относительный объём (30%)
    volume_ratio = volume_4h / avg_volume_20
    volume_component = (volume_ratio - 1) * 30
    
    # Компонент 2: CEX netflow (40%)
    # Положительный netflow = приток на биржи = bearish
    # Отрицательный netflow = отток с бирж = bullish
    netflow_norm = cex_netflow_1h / 1000  # Нормализация (предполагается среднее ~1000 ETH/час)
    netflow_component = -netflow_norm * 40  # Инвертируем знак
    
    # Компонент 3: Whale inflow (30%)
    # Положительный whale inflow = киты накапливают = bullish
    whale_norm = whale_inflow_4h / 500  # Нормализация (предполагается среднее ~500 ETH/4h)
    whale_component = whale_norm * 30
    
    # Итоговый score
    score = volume_component + netflow_component + whale_component
    return np.clip(score, -100, 100)
Интерпретация:

score > 0 → высокий объём + киты накапливают + отток с бирж (бычий)
score < 0 → низкий объём + киты продают + приток на биржи (bearish)
⚠️ ДЛЯ L1 (упрощённая версия без on-chain данных):

def calculate_volume_score_l1(volume_4h, avg_volume_20):
    """
    Упрощённая версия для L1 (только биржевой объём)
    """
    volume_ratio = volume_4h / avg_volume_20
    score = (volume_ratio - 1) * 100
    return np.clip(score, -100, 100)
2,3. Настроение (20%)
def calculate_sentiment(sentiment_eth_1h):
    """
    Sentiment уже предоставлен внешним источником в диапазоне -100..+100
    
    Вход:
        sentiment_eth_1h: индекс настроений для ETH (1H)
            Источник: Twitter/Reddit/News API (агрегированный)
    
    Выход:
        score: от -100 до +100 (без изменений)
    """
    return sentiment_eth_1h
⚠️ ДЛЯ L1 (временное предложение):

def calculate_sentiment_l1():
    """
    В L1 Sentiment отключён (возвращает 0)
    Будет реализован в L2 после подключения к API
    """
    return 0.0
2,4. BTC_Correlation (15%)
def calculate_btc_correlation(eth_returns_24h, btc_returns_24h):
    """
    Корреляция ETH с BTC за последние 24 часа + направление тренда BTC
    
    Вход:
        eth_returns_24h: массив returns ETH (24 последних 1H-бара)
        btc_returns_24h: массив returns BTC (24 последних 1H-бара)
    
    Выход:
        score: от -100 до +100
    """
    # Корреляция Пирсона
    corr = np.corrcoef(eth_returns_24h, btc_returns_24h)[0, 1]
    
    # Направление BTC (последний бар)
    btc_trend = np.sign(btc_returns_24h[-1])  # +1 (рост), -1 (падение), 0 (флэт)
    
    # Итоговый score
    # Если BTC растёт и корреляция высокая → bullish для ETH
    # Если BTC падает и корреляция высокая → bearish для ETH
    score = corr * btc_trend * 100
    return score
Интерпретация:

score > 0 → BTC растёт, ETH следует за ним (бычий)
score < 0 → BTC падает, ETH следует за ним (bearish)
score ≈ 0 → корреляция слабая или BTC флэт
⚠️ ДЛЯ L1 (упрощённая версия):

def calculate_btc_correlation_l1(btc_close_1h):
    """
    Упрощённая версия: только направление BTC (без корреляции)
    """
    btc_returns = np.diff(btc_close_1h[-24:]) / btc_close_1h[-25:-1]
    btc_trend = np.sign(btc_returns[-1])
    score = btc_trend * 50  # Половина от максимального веса (15%)
    return score
3️⃣ MOMENTUM_FACTOR (усиление сигнала)
def calculate_momentum_factor(close_1h, lookback_z=12):
    """
    Z-score момента для краткосрочного тренда
    
    Вход:
        close_1h: массив цен закрытия 1H-баров (последние N баров)
        lookback_z: окно для расчёта (по умолчанию 12 баров = 12 часов)
    
    Выход:
        momentum: от -100 до +100
    """
    # Расчёт returns за последние lookback_z баров
    returns = np.diff(close_1h[-lookback_z:]) / close_1h[-lookback_z:-1]
    
    # Средний return и стандартное отклонение
    avg_return = np.mean(returns)
    std_return = np.std(returns)
    
    # Z-score
    z_score = avg_return / std_return if std_return > 0 else 0
    
    # Нормализация через tanh
    momentum = np.tanh(z_score) * 100
    return momentum
Применение:

MASTER_SIGNAL_ADJUSTED = MASTER_SIGNAL + (Momentum_Factor × 0.10)
Интерпретация:

momentum > 0 → краткосрочный восходящий тренд (усиливает bullish сигнал)
momentum < 0 → краткосрочный нисходящий тренд (усиливает bearish сигнал)
4️⃣ VETO-ФИЛЬТРЫ (блокируют вход)
4.1. ATR-расширение (блокирует при высокой волатильности)
def atr_veto(atr_14_1h, atr_ma_50_1h):
    """
    Блокирует вход, если текущий ATR >> средний ATR
    (защита от входа в момент паники/памп-дампа)
    
    Вход:
        atr_14_1h: текущий ATR(14) на 1H
        atr_ma_50_1h: простая скользящая средняя ATR за 50 баров (1H)
    
    Выход:
        True = блокировать вход
        False = разрешить вход
    """
    if atr_14_1h > atr_ma_50_1h * 2.0:
        return True  # Блокировать
    return False
4.2. Volume-коллапс (блокирует при низком объёме)
def volume_veto(volume_4h, avg_volume_20):
    """
    Блокирует вход, если объём слишком низкий
    (защита от входа в иллюзорные движения при низкой ликвидности)
    
    Вход:
        volume_4h: текущий объём на 4H-баре
        avg_volume_20: средний объём за последние 20 баров (4H)
    
    Выход:
        True = блокировать вход
        False = разрешить вход
    """
    if volume_4h < avg_volume_20 * 0.3:
        return True  # Блокировать
    return False
5️⃣ РАЗМЕР ПОЗИЦИИ (Risk-Sizing)
def calculate_position_size(account_balance, entry_price, sl_price, risk_per_trade=0.01):
    """
    Расчёт размера позиции на основе риска
    
    Вход:
        account_balance: баланс счёта (USDT)
        entry_price: цена входа (USDT)
        sl_price: цена стоп-лосса (USDT)
        risk_per_trade: максимальный риск на сделку (по умолчанию 1% = 0.01)
    
    Выход:
        size: размер позиции (ETH)
    """
    # Расстояние до стоп-лосса (в процентах)
    distance_to_sl = abs(entry_price - sl_price) / entry_price
    
    # Максимально допустимая потеря (в USDT)
    max_loss_usd = account_balance * risk_per_trade
    
    # Размер позиции (ETH)
    size_eth = max_loss_usd / (entry_price * distance_to_sl)
    
    # Ограничение: не более 20% баланса в одной сделке
    max_size_eth = (account_balance * 0.20) / entry_price
    
    return min(size_eth, max_size_eth)
Пример:

Баланс = $10,000
Entry = $2,000
SL = $1,800 (10% от entry)
risk_per_trade = 1%

distance_to_sl = 0.10 (10%)
max_loss_usd = $100
size_eth = $100 / ($2,000 × 0.10) = 0.5 ETH
max_size_eth = ($10,000 × 0.20) / $2,000 = 1.0 ETH

Итого: size = min(0.5, 1.0) = 0.5 ETH
6️⃣ STOP-LOSS (адаптивный, на основе ATR)
def calculate_sl(entry_price, atr_14_1h, side, master_signal_adjusted, k_sl_min=1.5, k_sl_max=3.0):
    """
    Адаптивный стоп-лосс на основе силы сигнала
    
    Вход:
        entry_price: цена входа
        atr_14_1h: ATR(14) на 1H
        side: "LONG" или "SHORT"
        master_signal_adjusted: скорректированный MASTER_SIGNAL (с учётом Momentum)
        k_sl_min: минимальный коэффициент ATR (при сильном сигнале)
        k_sl_max: максимальный коэффициент ATR (при слабом сигнале)
    
    Выход:
        sl_price: цена стоп-лосса
    """
    # Сила сигнала (абсолютное значение)
    signal_strength = abs(master_signal_adjusted)
    
    # Адаптивный коэффициент k_sl
    # Чем сильнее сигнал → тем ближе стоп (k_sl_min)
    # Чем слабее сигнал → тем дальше стоп (k_sl_max)
    k_sl = k_sl_max - (signal_strength / 100) * (k_sl_max - k_sl_min)
    
    # Расчёт стоп-лосса
    if side == "LONG":
        sl_price = entry_price - (atr_14_1h * k_sl)
    else:  # SHORT
        sl_price = entry_price + (atr_14_1h * k_sl)
    
    return sl_price
Пример:

entry_price = $2,000
atr_14_1h = $50
master_signal_adjusted = 60 (сильный bullish)
side = "LONG"

signal_strength = 60
k_sl = 3.0 - (60/100) × (3.0 - 1.5) = 3.0 - 0.9 = 2.1

sl_price = $2,000 - ($50 × 2.1) = $2,000 - $105 = $1,895
7️⃣ TAKE-PROFIT (2-ступенчатый)
def calculate_tp(entry_price, atr_14_1h, side, k_tp1=2.0, k_tp2=4.0):
    """
    Два уровня тейк-профита
    
    Вход:
        entry_price: цена входа
        atr_14_1h: ATR(14) на 1H
        side: "LONG" или "SHORT"
        k_tp1: коэффициент ATR для TP1 (по умолчанию 2.0)
        k_tp2: коэффициент ATR для TP2 (по умолчанию 4.0)
    
    Выход:
        tp1: цена первого тейк-профита (закрыть 50% позиции)
        tp2: цена второго тейк-профита (закрыть оставшиеся 50%)
    """
    if side == "LONG":
        tp1 = entry_price + (atr_14_1h * k_tp1)
        tp2 = entry_price + (atr_14_1h * k_tp2)
    else:  # SHORT
        tp1 = entry_price - (atr_14_1h * k_tp1)
        tp2 = entry_price - (atr_14_1h * k_tp2)
    
    return tp1, tp2
Логика исполнения:

Позиция открыта: 100%
Цена достигла TP1 → закрыть 50% позиции, переместить SL (см. Остановка на трейлинге)
Цена достигла TP2 → закрыть оставшиеся 50%
8️⃣ TRAILING STOP-LOSS (после достижения TP1)
def trailing_stop(entry_price, atr_14_1h, side, k_tsl=1.0):
    """
    Перемещение стоп-лосса после достижения TP1
    
    Вход:
        entry_price: цена входа
        atr_14_1h: ATR(14) на 1H
        side: "LONG" или "SHORT"
        k_tsl: коэффициент ATR для TSL (по умолчанию 1.0)
    
    Выход:
        tsl_price: новая цена стоп-лосса (в безубыток + 1 ATR)
    """
    if side == "LONG":
        tsl_price = entry_price + (atr_14_1h * k_tsl)
    else:  # SHORT
        tsl_price = entry_price - (atr_14_1h * k_tsl)
    
    return tsl_price
Логика:

После достижения TP1, стоп-лосс перемещается на (для LONG)entry + 1 ATR
Это гарантирует минимальную прибыль даже если цена развернётся
9️⃣ ПОЛНАЯ ЛОГИКА ВХОДА (generate_signal)
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class Signal:
    strategy_id: str
    ts: pd.Timestamp
    symbol: str
    side: str          # "LONG" or "SHORT"
    size: float        # quantity (ETH)
    sl: float          # Stop-Loss price
    tp1: float         # Take-Profit 1 price
    tp2: float         # Take-Profit 2 price
    tsl: float | None  # Trailing Stop-Loss (устанавливается после TP1)
    valid_until: pd.Timestamp
    meta: dict

def generate_signal(features_row, account_balance, params):
    """
    Генерация сигнала для одного 4H-бара
    
    Вход:
        features_row: одна строка DataFrame с фичами (из lab.features_v1)
        account_balance: текущий баланс счёта (USDT)
        params: словарь параметров (PARAMS)
    
    Выход:
        signal: объект Signal или None
    """
    
    # 1. Расчёт компонентов MASTER_SIGNAL
    price_score = calculate_price_score(
        features_row["close_4h"],
        features_row["sma_50_4h"],
        features_row["atr_14_1h"]
    )
    
    volume_score = calculate_volume_score_l1(  # Упрощённая версия для L1
        features_row["volume_4h"],
        features_row["avg_volume_20"]
    )
    
    sentiment = calculate_sentiment_l1()  # Placeholder для L1 (вернёт 0)
    
    btc_corr = calculate_btc_correlation_l1(
        features_row["btc_close_1h_array"]
    )
    
    # 2. MASTER_SIGNAL
    master = (price_score * 0.35) + (volume_score * 0.30) + (sentiment * 0.20) + (btc_corr * 0.15)
    
    # 3. Momentum-усиление
    momentum = calculate_momentum_factor(
        features_row["close_1h_array"],
        lookback_z=params["lookback_z"]
    )
    master_adj = master + (momentum * 0.10)
    
    # 4. Veto-фильтры
    if atr_veto(features_row["atr_14_1h"], features_row["atr_ma_50_1h"]):
        return None  # Блокировать вход (высокая волатильность)
    
    if volume_veto(features_row["volume_4h"], features_row["avg_volume_20"]):
        return None  # Блокировать вход (низкий объём)
    
    # 5. Определение направления сигнала
    if master_adj > params["master_long_threshold"]:
        side = "LONG"
    elif master_adj < params["master_short_threshold"]:
        side = "SHORT"
    else:
        return None  # Нейтральная зона (без входа)
    
    # 6. Расчёт цены входа, SL, TP
    entry_price = features_row["close_4h"]
    
    sl = calculate_sl(
        entry_price,
        features_row["atr_14_1h"],
        side,
        master_adj,
        k_sl_min=params["k_sl_min"],
        k_sl_max=params["k_sl_max"]
    )
    
    tp1, tp2 = calculate_tp(
        entry_price,
        features_row["atr_14_1h"],
        side,
        k_tp1=params["k_tp1"],
        k_tp2=params["k_tp2"]
    )
    
    # 7. Расчёт размера позиции
    size = calculate_position_size(
        account_balance,
        entry_price,
        sl,
        risk_per_trade=params["risk_per_trade"]
    )
    
    # 8. Создание объекта Signal
    signal = Signal(
        strategy_id="STR-100",
        ts=features_row["ts_4h"],
        symbol="ETHUSDT",
        side=side,
        size=size,
        sl=sl,
        tp1=tp1,
        tp2=tp2,
        tsl=None,  # Устанавливается после достижения TP1
        valid_until=features_row["ts_4h"] + pd.Timedelta(hours=4),
        meta={
            "master_signal": master_adj,
            "momentum": momentum,
            "price_score": price_score,
            "volume_score": volume_score,
            "sentiment": sentiment,
            "btc_corr": btc_corr,
            "k_sl": calculate_k_sl(master_adj, params)  # Для анализа
        }
    )
    
    return signal

def calculate_k_sl(master_signal_adjusted, params):
    """Вспомогательная функция для расчёта k_sl"""
    signal_strength = abs(master_signal_adjusted)
    k_sl = params["k_sl_max"] - (signal_strength / 100) * (params["k_sl_max"] - params["k_sl_min"])
    return k_sl
🔟 ПАРАМЕТРЫ ПО УМОЛЧАНИЮ (для L1)
PARAMS = {
    # Risk Management
    "risk_per_trade": 0.01,        # 1% риска на сделку
    "max_position_pct": 0.20,      # Максимум 20% баланса в позиции
    
    # Stop-Loss / Take-Profit
    "k_sl_min": 1.5,               # Минимальный SL (1.5 ATR, при сильном сигнале)
    "k_sl_max": 3.0,               # Максимальный SL (3.0 ATR, при слабом сигнале)
    "k_tp1": 2.0,                  # TP1 (2 ATR, закрыть 50%)
    "k_tp2": 4.0,                  # TP2 (4 ATR, закрыть 50%)
    "k_tsl": 1.0,                  # Trailing SL (1 ATR от entry)
    
    # Signal Thresholds
    "master_long_threshold": 40,   # Порог для LONG
    "master_short_threshold": -40, # Порог для SHORT
    "lookback_z": 12,              # Окно для Momentum (12 баров 1H)
    
    # Veto Filters
    "atr_expansion_multiplier": 2.0,  # Veto при ATR > 2×MA
    "volume_collapse_multiplier": 0.3, # Veto при volume < 0.3×MA
    
    # Costs
    "commission_rate": 0.0004,     # 0.04% комиссия (Binance Futures)
    "slippage_bps": 5              # 0.05% slippage
}
✅ КРИТЕРИИ ДЕТЕРМИНИЗМА
Стратегия считается детерминированной, если:

✅ При одинаковых входных данных (features_row) → одинаковый сигнал
✅ Все параметры явно заданы (нет скрытых состояний)
✅ Все формулы математически точны (не используются случайные числа)
✅ Unit-тесты проходят с фиксированными входными данными
Unit-тест для проверки:

def test_str100_determinism():
    # Фиксированные входные данные
    features = {
        "ts_4h": pd.Timestamp("2024-01-01 00:00:00", tz="UTC"),
        "close_4h": 2000.0,
        "sma_50_4h": 1950.0,
        "atr_14_1h": 50.0,
        "volume_4h": 15000.0,
        "avg_volume_20": 12000.0,
        "atr_ma_50_1h": 45.0,
        "close_1h_array": np.array([1990, 1995, 2000, 2005, 2000, 1998, 2002, 2010, 2015, 2012, 2008, 2000]),
        "btc_close_1h_array": np.array([40000, 40100, 40200, 40300, 40250, 40200, 40400, 40500, 40600, 40550, 40500, 40450])
    }
    
    account_balance = 10000.0
    
    # Генерация сигнала дважды
    signal1 = generate_signal(features, account_balance, PARAMS)
    signal2 = generate_signal(features, account_balance, PARAMS)
    
    # Проверка детерминизма
    assert signal1.side == signal2.side
    assert signal1.size == signal2.size
    assert signal1.sl == signal2.sl
    assert signal1.tp1 == signal2.tp1
    assert signal1.tp2 == signal2.tp2
    assert signal1.meta["master_signal"] == signal2.meta["master_signal"]
📅 ВЕРСИЯ СТРАТЕГИИ
Версия: v3.2
Дата: 2025-11-24
Автор: arturklimovich-art
Статус: Спецификация для реализации в TradLab L1
Детерминизм: ✅ 100% (все формулы и параметры зафиксированы)
📝 ПРИМЕЧАНИЯ ДЛЯ РЕАЛИЗАЦИИ
Для L1 используются упрощённые версии:

Volume_Score без on-chain данных
Sentiment = 0 (placeholder)
BTC_Correlation упрощённая (без корреляции Пирсона)
Для L2 нужно добавить:

API для on-chain данных (cex_netflow, whale_inflow)
API для Sentiment (Twitter/Reddit/News)
Полную корреляцию с BTC
Backtester должен:

Использовать комиссии: 0.04% per side
Использовать slippage: 0.05%
Симулировать 2-ступенчатый TP (50% на TP1, 50% на TP2)
Симулировать Trailing Stop после достижения TP1
Unit-тесты должны проверять:

Детерминизм (одинаковые входы → одинаковые выходы)
Диапазоны значений (Score'ы в [-100, +100])
Veto-фильтры (блокируют при экстремальных условиях)
Risk-sizing (не превышает 1% риска и 20% баланса)
🎯 DoD ДЛЯ STR-100

Все формулы Score'ов задокументированы

MASTER_SIGNAL с точными коэффициентами

Momentum_Factor реализован

Veto-фильтры описаны

Risk-sizing с ограничениями

Адаптивный SL (зависит от силы сигнала)

2-ступенчатый TP (50% + 50%)

Trailing Stop-Loss после TP1

Все параметры зафиксированы в PARAMS

Unit-тест для проверки детерминизма
Стратегия готова к реализации! ✅
