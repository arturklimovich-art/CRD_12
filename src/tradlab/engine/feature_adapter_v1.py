import pandas as pd
import psycopg2
from typing import Optional


class FeatureAdapterV1:
    """
    Адаптер для извлечения и подготовки фич из БД
    
    Извлекает данные из lab.features_v1 и подготавливает их
    для передачи в стратегию.
    """
    
    def __init__(self, db_url: str):
        """
        Инициализация адаптера
        
        Args:
            db_url: PostgreSQL connection string
        """
        self.db_url = db_url
    
    def fetch_features(
        self, 
        symbol: str = "ETHUSDT",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Загрузка фич из lab.features_v1
        
        Args:
            symbol: Торговая пара
            start_date: Начальная дата (YYYY-MM-DD)
            end_date: Конечная дата (YYYY-MM-DD)
        
        Returns:
            DataFrame с фичами
        """
        query = """
        SELECT 
            symbol,
            ts_4h,
            open_4h,
            high_4h,
            low_4h,
            close_4h,
            volume_4h,
            close_1h
        FROM lab.features_v1
        WHERE symbol = %s
        """
        
        params = [symbol]
        
        if start_date:
            query += " AND ts_4h >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND ts_4h <= %s"
            params.append(end_date)
        
        query += " ORDER BY ts_4h ASC"
        
        with psycopg2.connect(self.db_url) as conn:
            df = pd.read_sql(query, conn, params=params)
        
        return df
    
    def prepare_features_for_strategy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Подготовка фич для передачи в стратегию
        
        Может добавлять вычисленные фичи (например, SMA, ATR)
        
        Args:
            df: DataFrame с сырыми фичами из БД
        
        Returns:
            DataFrame с подготовленными фичами
        """
        # В L1 просто возвращаем как есть
        # В L2 можно добавить расчёт SMA, ATR, и т.д.
        return df
