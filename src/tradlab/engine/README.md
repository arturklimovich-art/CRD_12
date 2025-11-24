# TradLab Engine

## Описание

Модуль `engine` содержит базовые компоненты для торговых стратегий:

- **Signal** — dataclass для торговых сигналов
- **BaseStrategy** — абстрактный базовый класс для всех стратегий
- **FeatureAdapterV1** — адаптер для извлечения фич из БД

---

## Использование

### Создание собственной стратегии

```python
from tradlab.engine import BaseStrategy, Signal
import pandas as pd

class MyStrategy(BaseStrategy):
    def generate_signal(self, features: pd.Series, account_balance: float):
        # Ваша логика генерации сигнала
        if features["close_4h"] > 2000:
            return Signal(
                strategy_id=self.strategy_id,
                ts=features["ts_4h"],
                symbol="ETHUSDT",
                side="LONG",
                size=1.0,
                sl=1900.0,
                tp1=2100.0,
                tp2=2200.0
            )
        return None
```

### Извлечение фич из БД

```python
from tradlab.engine import FeatureAdapterV1

adapter = FeatureAdapterV1(db_url="postgresql://user:pass@localhost:5432/db")
features = adapter.fetch_features(symbol="ETHUSDT", start_date="2024-01-01")
```
