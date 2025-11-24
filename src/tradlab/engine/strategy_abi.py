from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any, List
from .signal import Signal


class BaseStrategy(ABC):
    """
    Базовый абстрактный класс для всех торговых стратегий
    
    Все стратегии должны наследоваться от этого класса и реализовывать
    метод generate_signal().
    
    Attributes:
        strategy_id: Уникальный идентификатор стратегии
        params: Словарь параметров стратегии
    """
    
    def __init__(self, strategy_id: str, params: Dict[str, Any]):
        """
        Инициализация стратегии
        
        Args:
            strategy_id: Уникальный ID (например, "STR-100")
            params: Словарь параметров (например, PARAMS из спецификации)
        """
        self.strategy_id = strategy_id
        self.params = params
        self._validate_params()
    
    @abstractmethod
    def generate_signal(
        self, 
        features: pd.Series,
        account_balance: float
    ) -> Optional[Signal]:
        """
        Генерация торгового сигнала
        
        Args:
            features: Pandas Series с фичами (одна строка из lab.features_v1)
            account_balance: Текущий баланс счёта (USDT)
        
        Returns:
            Signal объект или None (если нет сигнала)
        
        Raises:
            NotImplementedError: Должен быть реализован в подклассе
        """
        raise NotImplementedError("Subclass must implement generate_signal()")
    
    def _validate_params(self):
        """
        Валидация параметров стратегии
        
        Может быть переопределён в подклассе для специфичной валидации
        """
        if not isinstance(self.params, dict):
            raise ValueError("params must be a dictionary")
    
    def get_required_features(self) -> List[str]:
        """
        Возвращает список необходимых фич для стратегии
        
        Может быть переопределён в подклассе
        
        Returns:
            Список названий колонок из lab.features_v1
        """
        return [
            "ts_4h",
            "symbol",
            "close_4h",
            "volume_4h"
        ]
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(strategy_id='{self.strategy_id}')"
