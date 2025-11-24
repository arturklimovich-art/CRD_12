"""
OHLCV Collector v0 - Загрузка исторических данных с Binance
Задача: E1-B2-T2 (TradLab L1)
Автор: arturklimovich-art
Дата: 2025-11-24
"""
import ccxt
import pandas as pd
import psycopg2
from datetime import datetime, timezone
import time
import logging
from typing import List, Optional


class OHLCVCollector:
    """
    Collector для загрузки OHLCV данных с Binance в PostgreSQL.

    Attributes:
        exchange: CCXT Binance exchange instance
        db_url: PostgreSQL connection string
        logger: Logger instance
    """

    def __init__(self, db_url: str):
        """
        Инициализация collector.

        Args:
            db_url: PostgreSQL connection string
                    (postgresql://user:password@host:port/dbname)
        """
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        self.db_url = db_url
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Настройка логгера.

        Returns:
            Настроенный logger instance
        """
        logger = logging.getLogger('OHLCVCollector')
        logger.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)

        # Avoid duplicate handlers
        if not logger.handlers:
            logger.addHandler(ch)

        return logger

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: datetime
    ) -> pd.DataFrame:
        """
        Загрузка OHLCV данных с Binance.

        Args:
            symbol: Торговая пара (например, "ETH/USDT")
            timeframe: Таймфрейм ("1h", "4h")
            since: Дата начала загрузки

        Returns:
            DataFrame с колонками: ts, open, high, low, close, volume
        """
        self.logger.info(
            f"Начало загрузки {symbol} {timeframe} с {since}"
        )

        # Конвертируем datetime в миллисекунды
        since_ms = int(since.timestamp() * 1000)

        all_ohlcv = []
        limit = 1000  # Максимум за один запрос

        while True:
            try:
                # Запрос к Binance
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    since=since_ms,
                    limit=limit
                )

                if not ohlcv:
                    break

                all_ohlcv.extend(ohlcv)

                # Проверяем, есть ли ещё данные
                last_timestamp = ohlcv[-1][0]
                if last_timestamp <= since_ms:
                    break

                # Обновляем стартовую точку
                since_ms = last_timestamp + 1

                self.logger.info(
                    f"Загружено {len(ohlcv)} свечей, "
                    f"всего: {len(all_ohlcv)}"
                )

                # Rate limiting - пауза между запросами
                time.sleep(0.1)

                # Если получили меньше limit, значит дошли до конца
                if len(ohlcv) < limit:
                    break

            except Exception as e:
                self.logger.error(f"Ошибка при загрузке данных: {e}")
                raise

        # Конвертируем в DataFrame
        df = pd.DataFrame(
            all_ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )

        # Конвертируем timestamp из миллисекунд в datetime UTC
        df['ts'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df = df.drop('timestamp', axis=1)

        # Переставляем колонки в нужном порядке
        df = df[['ts', 'open', 'high', 'low', 'close', 'volume']]

        self.logger.info(
            f"Загрузка завершена: {len(df)} свечей "
            f"({df['ts'].min()} - {df['ts'].max()})"
        )

        return df

    def save_to_db(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ):
        """
        Сохранение данных в PostgreSQL.

        Args:
            df: DataFrame с OHLCV данными
            symbol: Символ (ETHUSDT)
            timeframe: Таймфрейм (1h, 4h)
        """
        self.logger.info(
            f"Сохранение {len(df)} записей в БД "
            f"({symbol}, {timeframe})"
        )

        # Конвертируем ETH/USDT в ETHUSDT
        symbol_db = symbol.replace('/', '')

        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Подготавливаем данные для bulk insert
            records = []
            for _, row in df.iterrows():
                records.append((
                    symbol_db,
                    timeframe,
                    row['ts'],
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume']),
                    'binance'
                ))

            # Bulk insert с ON CONFLICT DO NOTHING
            insert_query = """
                INSERT INTO market.ohlcv
                (symbol, tf, ts, open, high, low, close, volume, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, tf, ts) DO NOTHING
            """

            cursor.executemany(insert_query, records)
            conn.commit()

            inserted_count = cursor.rowcount
            self.logger.info(
                f"Сохранено {inserted_count} новых записей "
                f"(дубликаты пропущены)"
            )

            cursor.close()
            conn.close()

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении в БД: {e}")
            raise

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Валидация данных (проверка пропусков, дубликатов).

        Args:
            df: DataFrame с OHLCV данными

        Returns:
            True если данные валидны
        """
        self.logger.info("Валидация данных...")

        # Проверка на пустой DataFrame
        if df.empty:
            self.logger.error("DataFrame пустой")
            return False

        # Проверка на NaN значения
        if df.isnull().any().any():
            null_counts = df.isnull().sum()
            self.logger.warning(f"Найдены NaN значения:\n{null_counts}")
            # Не фейлим, но логируем

        # Проверка на дубликаты по timestamp
        duplicates = df[df.duplicated(subset=['ts'], keep=False)]
        if not duplicates.empty:
            self.logger.warning(
                f"Найдено {len(duplicates)} дубликатов по timestamp"
            )
            # Не фейлим, дубликаты будут пропущены при insert

        # Проверка на правильность OHLCV
        # high должен быть >= low, open, close
        invalid_high = df[
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close'])
        ]
        if not invalid_high.empty:
            self.logger.error(
                f"Найдено {len(invalid_high)} записей "
                f"с некорректными значениями high"
            )
            return False

        # Проверка на правильность OHLCV
        # low должен быть <= high, open, close
        invalid_low = df[
            (df['low'] > df['high']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        ]
        if not invalid_low.empty:
            self.logger.error(
                f"Найдено {len(invalid_low)} записей "
                f"с некорректными значениями low"
            )
            return False

        # Проверка на отрицательные значения
        if (df[['open', 'high', 'low', 'close', 'volume']] < 0).any().any():
            self.logger.error("Найдены отрицательные значения")
            return False

        self.logger.info("✅ Данные валидны")
        return True

    def collect(
        self,
        symbol: str = "ETH/USDT",
        timeframes: List[str] = None,
        start_date: Optional[datetime] = None
    ):
        """
        Основной метод для загрузки данных.

        Args:
            symbol: Торговая пара
            timeframes: Список таймфреймов
            start_date: Дата начала (по умолчанию 2019-01-01)
        """
        if timeframes is None:
            timeframes = ["1h", "4h"]

        if start_date is None:
            start_date = datetime(2019, 1, 1, tzinfo=timezone.utc)

        self.logger.info(
            f"========================================\n"
            f"Запуск collector для {symbol}\n"
            f"Таймфреймы: {timeframes}\n"
            f"Период: с {start_date}\n"
            f"========================================"
        )

        for timeframe in timeframes:
            try:
                self.logger.info(f"\n--- Обработка {timeframe} ---")

                # Загрузка данных
                df = self.fetch_ohlcv(symbol, timeframe, start_date)

                # Валидация
                if not self.validate_data(df):
                    self.logger.error(
                        f"Валидация не пройдена для {timeframe}, "
                        f"пропускаем сохранение"
                    )
                    continue

                # Сохранение в БД
                self.save_to_db(df, symbol, timeframe)

                self.logger.info(f"✅ {timeframe} обработан успешно\n")

            except Exception as e:
                self.logger.error(
                    f"❌ Ошибка при обработке {timeframe}: {e}\n"
                )
                # Продолжаем со следующим timeframe
                continue

        self.logger.info(
            "========================================\n"
            "Collector завершил работу\n"
            "========================================"
        )
