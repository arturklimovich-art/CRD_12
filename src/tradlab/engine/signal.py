from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Signal:
    """
    Торговый сигнал от стратегии
    
    Attributes:
        strategy_id: Уникальный ID стратегии (например, "STR-100")
        ts: Timestamp генерации сигнала (UTC)
        symbol: Торговая пара (например, "ETHUSDT")
        side: Направление ("LONG" или "SHORT")
        size: Размер позиции (в базовой валюте, например ETH)
        sl: Цена Stop-Loss
        tp1: Цена Take-Profit 1 (закрыть 50% позиции)
        tp2: Цена Take-Profit 2 (закрыть оставшиеся 50%)
        tsl: Trailing Stop-Loss (устанавливается после достижения TP1)
        valid_until: Сигнал действителен до этого времени
        meta: Дополнительные метаданные (словарь)
    """
    strategy_id: str
    ts: datetime
    symbol: str
    side: str  # "LONG" or "SHORT"
    size: float
    sl: float
    tp1: float
    tp2: float
    tsl: Optional[float] = None
    valid_until: Optional[datetime] = None
    meta: dict = None
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if self.side not in ["LONG", "SHORT"]:
            raise ValueError(f"Invalid side: {self.side}. Must be 'LONG' or 'SHORT'")
        
        if self.size <= 0:
            raise ValueError(f"Invalid size: {self.size}. Must be > 0")
        
        if self.meta is None:
            self.meta = {}
    
    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return {
            "strategy_id": self.strategy_id,
            "ts": self.ts.isoformat(),
            "symbol": self.symbol,
            "side": self.side,
            "size": self.size,
            "sl": self.sl,
            "tp1": self.tp1,
            "tp2": self.tp2,
            "tsl": self.tsl,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "meta": self.meta
        }
