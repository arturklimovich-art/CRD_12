# 📘 PASSPORT ДОМЕНА TL (TradLab)

## 🎯 Назначение
TradLab — система разработки, бэктестинга и автоматизированной торговли стратегиями на криптовалютных рынках.

## 📊 Этап L1: Фундамент
**Цель этапа L1:**
1. Загрузка исторических данных (OHLCV ETHUSDT, 5+ лет)
2. Реализация стратегии STR-100 ChainFlow Alpha v3.2
3. Бэктестинг с метриками (PnL, Sharpe, Sortino, MaxDD, Calmar, WinRate, ProfitFactor)
4. Проверка через Risk-Gate (MinTRL, PSR, DSR, PBO)
5. Подключение к demo-счёту биржи для paper-trading

## 🗄️ Схемы БД
- **market**: Рыночные данные (market.ohlcv)
- **lab**: Бэктесты, сделки, результаты (lab.trades, lab.results, lab.jobs)

## 🛠️ Основные сервисы
- `src/tradlab/collector/` — Загрузка OHLCV с бирж
- `src/tradlab/engine/` — Strategy-ABI, Backtester, Метрики, Risk-Gate
- `src/tradlab/executor/` — Demo-Executor (подключение к testnet)
- `src/tradlab/bot/` — CLI-оркестратор (команды tradlab)

## 🟢 Зелёный коридор TL
```
/app/src/tradlab/
/app/workspace/specs/
/app/workspace/reports/TL/
/app/workspace/patches/DB/
ROADMAP/DOMAINS/TL/
```

## 📋 Шаблоны
- `/app/workspace/templates/ADR-template.md`
- `/app/workspace/templates/Checklist-template.md`

## 📅 Версия
- **Версия:** 0.2.0-L1
- **Дата:** 2025-11-24
- **Владелец:** arturklimovich-art
- **Статус:** in_progress

## 📞 Контакты
- **Repository:** https://github.com/arturklimovich-art/CRD_12
- **Issues:** https://github.com/arturklimovich-art/CRD_12/issues