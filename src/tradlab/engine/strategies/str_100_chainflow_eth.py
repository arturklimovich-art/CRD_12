import numpy as np
import pandas as pd
import logging
from typing import Optional
from ..strategy_abi import BaseStrategy
from ..signal import Signal


class STR100ChainFlowETH(BaseStrategy):
    """
    STR-100: ChainFlow Alpha v3.2
    
    Ð“Ð¸Ð±Ñ€Ð¸Ð´Ð½Ð°Ñ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ñ Ð´Ð»Ñ ETHUSDT Ñ ÑƒÐ¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¸ÐµÐ¼ ÑÐ¾Ð±Ñ‹Ñ‚Ð¸ÑÐ¼Ð¸.
    100% Ð´ÐµÑ‚ÐµÑ€Ð¼Ð¸Ð½Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð½Ð°Ñ Ñ€ÐµÐ°Ð»Ð¸Ð·Ð°Ñ†Ð¸Ñ.
    """
    
    # ÐŸÐ°Ñ€Ð°Ð¼ÐµÑ‚Ñ€Ñ‹ Ð¿Ð¾ ÑƒÐ¼Ð¾Ð»Ñ‡Ð°Ð½Ð¸ÑŽ
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
    
    # Exchange constraints for position sizing
    EXCHANGE_CONSTRAINTS = {
        'min_lot_size': 0.001,
        'max_lot_size': 9000.0,
        'lot_precision': 3,
        'min_notional': 10.0,
        'tick_size': 0.01
    }
    
    def __init__(self, strategy_id: str = "STR-100", params: dict = None):
        if params is None:
            params = self.PARAMS.copy()
        super().__init__(strategy_id, params)
        self._validate_params()
    
    def _validate_params(self):
        """Validate strategy parameters"""
        assert 0 < self.params["risk_per_trade"] <= 0.05, "risk_per_trade must be between 0 and 0.05"
        assert 0 < self.params["max_position_pct"] <= 0.50, "max_position_pct must be between 0 and 0.50"
        assert self.params["k_sl_min"] < self.params["k_sl_max"], "k_sl_min must be less than k_sl_max"
        assert self.params["k_tp1"] < self.params["k_tp2"], "k_tp1 must be less than k_tp2"
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Parameters validated")
    
    def generate_signal(self, features: pd.Series, account_balance: float) -> Optional[Signal]:
        """
        Ð“ÐµÐ½ÐµÑ€Ð°Ñ†Ð¸Ñ Ñ‚Ð¾Ñ€Ð³Ð¾Ð²Ð¾Ð³Ð¾ ÑÐ¸Ð³Ð½Ð°Ð»Ð°
        
        Args:
            features: Pandas Series Ñ Ñ„Ð¸Ñ‡Ð°Ð¼Ð¸
            account_balance: Ð‘Ð°Ð»Ð°Ð½Ñ ÑÑ‡Ñ‘Ñ‚Ð° (USDT)
        
        Returns:
            Signal Ð¸Ð»Ð¸ None
        """
        # 1. Ð Ð°ÑÑ‡Ñ‘Ñ‚ Score'Ð¾Ð²
        price_score = self._calculate_price_score(features)
        volume_score = self._calculate_volume_score_l1(features)
        
        # 2. MASTER_SIGNAL (rebalanced weights - removed placeholders)
        # Old: price_score * 0.35 + volume_score * 0.30 + sentiment * 0.20 + btc_corr * 0.15 + momentum * 0.10
        # New: Only use implemented components, rebalanced to sum to 1.0
        master = (
            price_score * 0.60 +    # 35/(35+30) = 0.636 ≈ 0.60
            volume_score * 0.40     # 30/(35+30) = 0.364 ≈ 0.40
        )
        
        # 3. Veto-Ñ„Ð¸Ð»ÑŒÑ‚Ñ€Ñ‹
        if self._atr_veto(features):
            return None
        
        if self._volume_veto(features):
            return None
        
        # 5. ÐžÐ¿Ñ€ÐµÐ´ÐµÐ»ÐµÐ½Ð¸Ðµ Ð½Ð°Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¸Ñ
        if master > self.params["master_long_threshold"]:
            side = "LONG"
        elif master < self.params["master_short_threshold"]:
            side = "SHORT"
        else:
            return None
        
        # 6. Ð Ð°ÑÑ‡Ñ‘Ñ‚ SL, TP
        entry_price = features["close_4h"]
        atr = features.get("atr_14_1h", 50.0)  # fallback ÐµÑÐ»Ð¸ Ð½ÐµÑ‚ ATR
        
        sl = self._calculate_sl(entry_price, atr, side, master)
        tp1, tp2 = self._calculate_tp(entry_price, atr, side)
        
        # 7. Ð Ð°Ð·Ð¼ÐµÑ€ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸
        size = self._calculate_position_size_safe(account_balance, entry_price, sl)
        
        # 8. Ð¡Ð¾Ð·Ð´Ð°Ð½Ð¸Ðµ Signal
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
                "master_signal": master,
                "price_score": price_score,
                "volume_score": volume_score
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
        """Volume Score L1 (ÑƒÐ¿Ñ€Ð¾Ñ‰Ñ‘Ð½Ð½Ð°Ñ Ð²ÐµÑ€ÑÐ¸Ñ, 30%)"""
        volume = features["volume_4h"]
        avg_volume = features.get("avg_volume_20", volume)
        
        volume_ratio = volume / avg_volume
        score = (volume_ratio - 1) * 100
        return float(np.clip(score, -100, 100))
    
    def _calculate_sentiment_l1(self) -> float:
        """Sentiment L1 (placeholder, 20%)"""
        return 0.0


    
    def _calculate_btc_correlation_l2(self, features: pd.Series) -> float:
        """
        BTC Correlation L2 (полная версия, 15%)
        
        Рассчитывает корреляцию ETH/BTC за последние 24 бара (1H)
        Положительная корреляция → ETH следует за BTC
        Отрицательная → расхождение (осторожно)
        """
        try:
            # Получаем timestamp текущего бара
            timestamp = features.name if isinstance(features.name, pd.Timestamp) else pd.Timestamp.now()
            
            # Загружаем BTC close array (24 бара назад)
            btc_closes = self.btc_provider.get_btc_close_array(timestamp, lookback=24)
            
            if btc_closes is None or len(btc_closes) < 24:
                # Fallback на L1 версию
                return self._calculate_btc_correlation_l1_fallback(features)
            
            # TODO: Нужен массив ETH closes за те же 24 бара
            # Пока используем упрощённую версию через price_score
            
            # Рассчитываем returns BTC
            btc_returns = np.diff(btc_closes) / btc_closes[:-1]
            
            # Направление BTC (положительный momentum = рост)
            btc_momentum = np.mean(btc_returns[-12:])  # последние 12 часов
            
            # Нормализуем через tanh → [-100, +100]
            btc_score = np.tanh(btc_momentum * 100) * 100
            
            return float(np.clip(btc_score, -100, 100))
        
        except Exception as e:
            # При ошибке возвращаем fallback
            return self._calculate_btc_correlation_l1_fallback(features)
    
    def _calculate_btc_correlation_l1_fallback(self, features: pd.Series) -> float:
        """Fallback L1 версия (аппроксимация через market momentum)"""
        price_score = self._calculate_price_score(features)
        volume_score = self._calculate_volume_score_l1(features)
        btc_proxy = (price_score * 0.6 + volume_score * 0.4) * 0.5
        return float(np.clip(btc_proxy, -100, 100))
    
    
    # ===== VETO FILTERS =====
    

    def _calculate_momentum_factor(self, features: pd.Series) -> float:
        """Momentum Factor (10%) - упрощённая версия через Price Score"""
        price_score = self._calculate_price_score(features)
        momentum = price_score * 0.3
        return float(np.clip(momentum, -100, 100))
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
    
    def _get_atr_with_fallback(self, features: pd.Series) -> float:
        """
        Get ATR with dynamic fallback
        
        Args:
            features: Feature series
        
        Returns:
            ATR value or fallback (2% of current price)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if "atr_14_1h" in features and not pd.isna(features["atr_14_1h"]):
            return features["atr_14_1h"]
        
        # Fallback: 2% of current price
        fallback = features["close_4h"] * 0.02
        logger.warning(f"ATR missing, using {fallback:.2f} (2% of price)")
        return fallback
    
    def _calculate_position_size_safe(self, balance: float, entry: float, sl: float) -> float:
        """
        Risk-based position sizing with exchange constraints
        
        Args:
            balance: Account balance (USDT)
            entry: Entry price
            sl: Stop-loss price
        
        Returns:
            Position size (in base currency) respecting exchange constraints
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Risk-based sizing
        distance_to_sl = abs(entry - sl) / entry
        max_loss = balance * self.params["risk_per_trade"]
        
        size = max_loss / (entry * distance_to_sl)
        max_size = (balance * self.params["max_position_pct"]) / entry
        size = min(size, max_size)
        
        # Apply exchange constraints
        size = max(size, self.EXCHANGE_CONSTRAINTS['min_lot_size'])
        size = min(size, self.EXCHANGE_CONSTRAINTS['max_lot_size'])
        size = round(size, self.EXCHANGE_CONSTRAINTS['lot_precision'])
        
        # Min notional check
        notional = size * entry
        if notional < self.EXCHANGE_CONSTRAINTS['min_notional']:
            logger.warning(f"Below min notional: {notional:.2f} < {self.EXCHANGE_CONSTRAINTS['min_notional']}")
            return 0.0
        
        return size










