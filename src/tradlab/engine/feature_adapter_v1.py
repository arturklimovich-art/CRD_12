import pandas as pd
import psycopg2
import logging
from typing import Optional

logger = logging.getLogger(__name__)


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
            close_1h,
            atr_14_1h,
            sma_50_4h,
            avg_volume_20
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
    
    def get_features(self, ts: pd.Timestamp, df: pd.DataFrame = None) -> Optional[pd.Series]:
        """
        Get features for a specific timestamp with validation
        
        Args:
            ts: Timestamp to get features for
            df: Optional DataFrame to search in (if None, will fetch from DB)
        
        Returns:
            Features as Series or None if not found/invalid
        """
        try:
            if df is None:
                # Fetch from database
                df = self.fetch_features()
            
            # Try to get features for timestamp
            if ts not in df.index:
                # If DataFrame doesn't have timestamp as index, try to find in ts_4h column
                if 'ts_4h' in df.columns:
                    df = df.set_index('ts_4h')
            
            features = df.loc[ts]
            
            # Validate required features
            required = ["close_4h", "volume_4h", "ts_4h"]
            missing = []
            
            for f in required:
                if f not in features.index:
                    missing.append(f)
                elif pd.isna(features[f]):
                    missing.append(f)
            
            if missing:
                logger.error(f"Missing or NaN features: {missing}")
                raise ValueError(f"Missing features: {missing}")
            
            return features
            
        except KeyError:
            logger.error(f"No features for timestamp {ts}")
            return None
        except Exception as e:
            logger.error(f"Feature error: {e}")
            return None
