# TradLab Engine

## Описание

Модуль `engine` содержит базовые компоненты для торговых стратегий:

- **Signal** — dataclass для торговых сигналов
- **BaseStrategy** — абстрактный базовый класс для всех стратегий
- **FeatureAdapterV1** — адаптер для извлечения фич из БД
- **MetricsCalculator** — класс для расчёта метрик торговых стратегий
- **BacktesterV1** — бэктестер для прогона стратегий на исторических данных

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

---

## Backtester v1

### Обзор

BacktesterV1 — это бэктестер для прогона торговых стратегий на исторических данных.

**Основные возможности:**
- Загрузка фич из БД через FeatureAdapterV1
- Прогон стратегии на каждом баре
- Симуляция исполнения трейдов с учётом комиссий и проскальзывания
- Расчёт метрик (Sharpe, Sortino, MaxDD, Calmar, Win Rate, Profit Factor)
- Сохранение трейдов в `lab.trades`
- Сохранение результатов в `lab.results`
- Проверка Risk Gate (Sharpe >= 1.0, MaxDD <= 20%, Win Rate >= 40%)

### Базовый пример использования

```python
from tradlab.engine import BacktesterV1
from tradlab.engine.strategies import STR100ChainFlowETH

# Создание стратегии
strategy = STR100ChainFlowETH(strategy_id="STR-100")

# Создание бэктестера
backtester = BacktesterV1(
    db_url="postgresql://user:pass@localhost:5432/tradlab_db",
    strategy=strategy,
    initial_capital=10000.0,
    commission_rate=0.0004,  # 0.04%
    slippage_bps=5.0  # 5 базисных пунктов
)

# Запуск бэктеста
results = backtester.run(
    symbol="ETHUSDT",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Просмотр результатов
print(f"Total PnL: {results['pnl_total']:.2f} USDT")
print(f"Sharpe Ratio: {results['sharpe']:.2f}")
print(f"Max Drawdown: {results['max_dd']:.2f}%")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Profit Factor: {results['profit_factor']:.2f}")
print(f"Risk Gate: {'PASS' if results['pass_risk_gate'] else 'FAIL'}")
```

### Результаты бэктеста

Метод `run()` возвращает словарь с результатами:

```python
{
    "run_id": "STR-100_20240101_120000_abc123",
    "strategy_id": "STR-100",
    "start_ts": "2024-01-01 00:00:00+00",
    "end_ts": "2024-12-31 23:59:59+00",
    "pnl_total": 2500.50,
    "sharpe": 1.85,
    "sortino": 2.10,
    "max_dd": 12.5,
    "calmar": 2.0,
    "win_rate": 55.0,
    "profit_factor": 2.3,
    "pass_risk_gate": True,
    "total_trades": 42
}
```

### Сохранение в БД

Бэктестер автоматически сохраняет результаты в БД:

**lab.trades** — все сделки с деталями:
- entry/exit timestamp и price
- PnL и PnL%
- Метаданные (причина закрытия, комиссии и т.д.)

**lab.results** — агрегированные метрики:
- Все метрики производительности
- Risk Gate статус
- Метаданные прогона

---

## MetricsCalculator

### Обзор

MetricsCalculator предоставляет статические методы для расчёта метрик торговых стратегий.

### Доступные метрики

#### Sharpe Ratio

```python
from tradlab.engine import MetricsCalculator
import pandas as pd

returns = pd.Series([0.01, 0.02, -0.005, 0.015, 0.012])
sharpe = MetricsCalculator.calculate_sharpe(returns, risk_free_rate=0.0)
print(f"Sharpe Ratio: {sharpe:.2f}")
```

#### Sortino Ratio

```python
sortino = MetricsCalculator.calculate_sortino(returns, risk_free_rate=0.0)
print(f"Sortino Ratio: {sortino:.2f}")
```

#### Maximum Drawdown

```python
equity_curve = pd.Series([10000, 10500, 10200, 9800, 10300, 10800])
max_dd = MetricsCalculator.calculate_max_drawdown(equity_curve)
print(f"Max Drawdown: {max_dd:.2f}%")
```

#### Calmar Ratio

```python
total_return_pct = 25.5  # 25.5% годовой доход
max_dd = 10.0  # 10% максимальная просадка
calmar = MetricsCalculator.calculate_calmar(total_return_pct, max_dd)
print(f"Calmar Ratio: {calmar:.2f}")
```

#### Win Rate

```python
trades = [
    {"pnl": 100},
    {"pnl": -50},
    {"pnl": 80},
    {"pnl": -40}
]
win_rate = MetricsCalculator.calculate_win_rate(trades)
print(f"Win Rate: {win_rate:.2f}%")
```

#### Profit Factor

```python
profit_factor = MetricsCalculator.calculate_profit_factor(trades)
print(f"Profit Factor: {profit_factor:.2f}")
```

---

## Risk Gate

Risk Gate — это набор критериев, которые стратегия должна пройти перед использованием в production.

### Критерии для L1:

1. **Sharpe Ratio >= 1.0** — Доходность с поправкой на риск
2. **Max Drawdown <= 20%** — Максимальная просадка не более 20%
3. **Win Rate >= 40%** — Минимум 40% прибыльных сделок

Если стратегия проходит все критерии, `pass_risk_gate = True`.

### Пример проверки

```python
results = backtester.run(...)

if results['pass_risk_gate']:
    print("✅ Стратегия прошла Risk Gate")
    print("Можно использовать на demo или production")
else:
    print("❌ Стратегия НЕ прошла Risk Gate")
    print("Требуется доработка")
    
    # Проверка конкретных метрик
    if results['sharpe'] < 1.0:
        print(f"  - Sharpe слишком низкий: {results['sharpe']:.2f}")
    if results['max_dd'] > 20.0:
        print(f"  - MaxDD слишком высокий: {results['max_dd']:.2f}%")
    if results['win_rate'] < 40.0:
        print(f"  - Win Rate слишком низкий: {results['win_rate']:.2f}%")
```

---

## Дополнительная информация

- **DataContract**: См. `ROADMAP/DOMAINS/TL/specs/DataContract.md`
- **StrategyABI**: См. `ROADMAP/DOMAINS/TL/specs/StrategyABI.md`
- **General Plan**: См. `ROADMAP/DOMAINS/TL/GENERAL_PLAN.yaml`
