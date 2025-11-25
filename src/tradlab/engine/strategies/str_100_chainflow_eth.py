import numpy as np
import pandas as pd
from typing import Optional
from ..strategy_abi import BaseStrategy
from ..signal import Signal


class STR100ChainFlowETH(BaseStrategy):
    """
    STR-100: ChainFlow Alpha v3.2
    
    Гибридная стратегия для ETHUSDT с управлением событиями.
    100% детерминированная реализация.
    """
    
    # Параметры по умолчанию
    PARAMS = {
        # Risk Management
        "risk_per_trade": 0.01,
        "max_position_pct": 0.20,
        
        # Stop-Loss / Take-Profit
        "k_sl_min": 1.5,
        "k_sl_max": 3.0,
        "k_tp1": 2.0,
        "k_tp2": 4.0,
        "k_tsl": 1.0,
        
        # Signal Thresholds
        "master_long_threshold": 15,
        "master_short_threshold": -15,
        "lookback_z": 12,
        
        # Veto Filters
        "atr_expansion_multiplier": 2.0,
        "volume_collapse_multiplier": 0.3,
        
        # Costs
        "commission_rate": 0.0004,
        "slippage_bps": 5
    }
    
    def __init__(self, strategy_id: str = "STR-100", params: dict = None):
        if params is None:
            params = self.PARAMS.copy()
        super().__init__(strategy_id, params)
    
    def generate_signal(self, features: pd.Series, account_balance: float) -> Optional[Signal]:
        """
        Генерация торгового сигнала
        
        Args:
            features: Pandas Series с фичами
            account_balance: Баланс счёта (USDT)
        
        Returns:
            Signal или None
        """
        # 1. Расчёт Score'ов
        price_score = self._calculate_price_score(features)
        volume_score = self._calculate_volume_score_l1(features)
        sentiment = self._calculate_sentiment_l1()
        btc_corr = self._calculate_btc_correlation_l1(features)
        
        # 2. MASTER_SIGNAL
        master = (
            price_score * 0.35 +
            volume_score * 0.30 +
            sentiment * 0.20 +
            btc_corr * 0.15
        )
        
        # 3. Momentum Factor
        momentum = self._calculate_momentum_factor(features)
        master_adj = master + (momentum * 0.10)
        
        # 4. Veto-фильтры
        if self._atr_veto(features):
            return None
        
        if self._volume_veto(features):
            return None
        
        # 5. Определение направления
        if master_adj > self.params["master_long_threshold"]:
            side = "LONG"
        elif master_adj < self.params["master_short_threshold"]:
            side = "SHORT"
        else:
            return None
        
        # 6. Расчёт SL, TP
        entry_price = features["close_4h"]
        atr = features.get("atr_14_1h", 50.0)  # fallback если нет ATR
        
        sl = self._calculate_sl(entry_price, atr, side, master_adj)
        tp1, tp2 = self._calculate_tp(entry_price, atr, side)
        
        # 7. Размер позиции
        size = self._calculate_position_size(account_balance, entry_price, sl)
        
        # 8. Создание Signal
        signal = Signal(
            strategy_id=self.strategy_id,
            ts=features["ts_4h"],
            symbol="ETHUSDT",
            side=side,
            size=size,
            sl=sl,
            tp1=tp1,
            tp2=tp2,
            tsl=None,
            valid_until=features["ts_4h"] + pd.Timedelta(hours=4),
            meta={
                "master_signal": master_adj,
                "momentum": momentum,
                "price_score": price_score,
                "volume_score": volume_score,
                "sentiment": sentiment,
                "btc_corr": btc_corr
            }
        )
        
        return signal
    
    # ===== SCORE FUNCTIONS =====
    
    def _calculate_price_score(self, features: pd.Series) -> float:
        """Price Score (35%)"""
        close = features["close_4h"]
        sma = features.get("sma_50_4h", close)  # fallback
        atr = features.get("atr_14_1h", 50.0)
        
        distance = (close - sma) / atr
        score = np.tanh(distance / 2) * 100
        return float(score)
    
    def _calculate_volume_score_l1(self, features: pd.Series) -> float:
        """Volume Score L1 (упрощённая версия, 30%)"""
        volume = features["volume_4h"]
        avg_volume = features.get("avg_volume_20", volume)
        
        volume_ratio = volume / avg_volume
        score = (volume_ratio - 1) * 100
        return float(np.clip(score, -100, 100))
    
    def _calculate_sentiment_l1(self) -> float:
        """Sentiment L1 (placeholder, 20%)"""
        return 0.0
    
    def _calculate_btc_correlation_l1(self, features: pd.Series) -> float:
        """BTC Correlation L1 (упрощённая, 15%)"""
        # В L1 используем только направление BTC
        # Требуется массив close_1h для BTC (пока используем 0)
        return 0.0
    
    def _calculate_momentum_factor(self, features: pd.Series) -> float:
        """Momentum Factor (10%)"""
        # Требуется массив close_1h_array (пока используем simple momentum)
        return 0.0
    
    # ===== VETO FILTERS =====
    
    def _atr_veto(self, features: pd.Series) -> bool:
        """ATR expansion veto"""
        atr = features.get("atr_14_1h", 50.0)
        atr_ma = features.get("atr_ma_50_1h", atr)
        
        multiplier = self.params["atr_expansion_multiplier"]
        return atr > atr_ma * multiplier
    
    def _volume_veto(self, features: pd.Series) -> bool:
        """Volume collapse veto"""
        volume = features["volume_4h"]
        avg_volume = features.get("avg_volume_20", volume)
        
        multiplier = self.params["volume_collapse_multiplier"]
        return volume < avg_volume * multiplier
    
    # ===== RISK MANAGEMENT =====
    
    def _calculate_position_size(self, balance: float, entry: float, sl: float) -> float:
        """Risk-based position sizing"""
        distance_to_sl = abs(entry - sl) / entry
        max_loss = balance * self.params["risk_per_trade"]
        
        size = max_loss / (entry * distance_to_sl)
        max_size = (balance * self.params["max_position_pct"]) / entry
        
        return min(size, max_size)
    
    def _calculate_sl(self, entry: float, atr: float, side: str, master_adj: float) -> float:
        """Adaptive Stop-Loss"""
        signal_strength = abs(master_adj)
        
        k_sl_min = self.params["k_sl_min"]
        k_sl_max = self.params["k_sl_max"]
        k_sl = k_sl_max - (signal_strength / 100) * (k_sl_max - k_sl_min)
        
        if side == "LONG":
            return entry - (atr * k_sl)
        else:
            return entry + (atr * k_sl)
    
    def _calculate_tp(self, entry: float, atr: float, side: str) -> tuple:
        """2-stage Take-Profit"""
        k_tp1 = self.params["k_tp1"]
        k_tp2 = self.params["k_tp2"]
        
        if side == "LONG":
            tp1 = entry + (atr * k_tp1)
            tp2 = entry + (atr * k_tp2)
        else:
            tp1 = entry - (atr * k_tp1)
            tp2 = entry - (atr * k_tp2)
        
        return tp1, tp2
