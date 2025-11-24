# OHLCV Collector v0

## Описание
Модуль для загрузки исторических OHLCV данных с Binance.

## Использование

### Пример 1: Загрузка ETHUSDT (1h, 4h) за последние 5 лет

```python
from tradlab.collector import OHLCVCollector

# Инициализация
collector = OHLCVCollector(
    db_url="postgresql://tradlab:password@localhost:5432/tradlab_db"
)

# Загрузка данных
collector.collect(
    symbol="ETH/USDT",
    timeframes=["1h", "4h"]
)
```

### Переменные окружения

Создайте файл `.env`:
```
DATABASE_URL=postgresql://tradlab:password@localhost:5432/tradlab_db
```

## Логи

Логи выводятся в консоль с информацией о прогрессе загрузки.

## Технические детали

### Формат данных в БД

Таблица `market.ohlcv`:
- `symbol`: "ETHUSDT" (без "/")
- `tf`: "1h" или "4h"
- `ts`: TIMESTAMPTZ в UTC
- `open`, `high`, `low`, `close`, `volume`: DOUBLE PRECISION
- `source`: "binance"

### Rate Limits

- Максимум 1200 запросов в минуту
- Используется: sleep 0.1s между запросами
- Встроенный rate limiter CCXT

### Обработка дубликатов

Используется `ON CONFLICT (symbol, tf, ts) DO NOTHING` в SQL - дубликаты автоматически пропускаются.

### Валидация данных

- Проверка на NaN значения
- Проверка корректности OHLCV (high >= low, open, close)
- Проверка на отрицательные значения
- Проверка на дубликаты timestamp
