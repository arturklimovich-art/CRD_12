-- ============================================================================
-- Миграция: 20251124_003_tl_schema_l1.sql
-- Задача: E1-B2-T1-S1 - SQL-миграция схем БД TradLab L1
-- Автор: arturklimovich-art
-- Дата: 2025-11-24
-- Описание: Создание схем market и lab для TradLab
-- ============================================================================

-- ============================================================================
-- 1. СХЕМА: market - Рыночные данные
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS market;

COMMENT ON SCHEMA market IS 'Схема для хранения рыночных данных (OHLCV)';

-- ============================================================================
-- 2. ТАБЛИЦА: market.ohlcv - OHLCV данные с бирж
-- ============================================================================
CREATE TABLE IF NOT EXISTS market.ohlcv (
  id      BIGSERIAL PRIMARY KEY,
  symbol  TEXT NOT NULL,           -- "ETHUSDT"
  tf      TEXT NOT NULL,           -- "1h", "4h"
  ts      TIMESTAMPTZ NOT NULL,    -- UTC timestamp
  open    DOUBLE PRECISION NOT NULL,
  high    DOUBLE PRECISION NOT NULL,
  low     DOUBLE PRECISION NOT NULL,
  close   DOUBLE PRECISION NOT NULL,
  volume  DOUBLE PRECISION NOT NULL,
  source  TEXT NOT NULL,           -- "binance"
  UNIQUE (symbol, tf, ts)
);

COMMENT ON TABLE market.ohlcv IS 'Хранение OHLCV данных с бирж';
COMMENT ON COLUMN market.ohlcv.symbol IS 'Торговая пара (например, ETHUSDT)';
COMMENT ON COLUMN market.ohlcv.tf IS 'Таймфрейм: 1h, 4h, 1d, etc.';
COMMENT ON COLUMN market.ohlcv.ts IS 'Временная метка в UTC';
COMMENT ON COLUMN market.ohlcv.source IS 'Источник данных (binance, etc.)';

-- Индекс для быстрого поиска по символу, таймфрейму и времени
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_tf_ts
  ON market.ohlcv(symbol, tf, ts);

-- ============================================================================
-- 3. СХЕМА: lab - Бэктесты и результаты
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS lab;

COMMENT ON SCHEMA lab IS 'Схема для хранения результатов бэктестов и торговли';

-- ============================================================================
-- 4. ТАБЛИЦА: lab.trades - Хранение всех сделок
-- ============================================================================
CREATE TABLE IF NOT EXISTS lab.trades (
  trade_id    BIGSERIAL PRIMARY KEY,
  run_id      TEXT NOT NULL,
  strategy_id TEXT NOT NULL,       -- "STR-100"
  mode        TEXT NOT NULL,       -- "backtest" | "demo"
  symbol      TEXT NOT NULL,
  side        TEXT NOT NULL,       -- "LONG" | "SHORT"
  qty         DOUBLE PRECISION NOT NULL,
  entry_ts    TIMESTAMPTZ NOT NULL,
  entry_price DOUBLE PRECISION NOT NULL,
  exit_ts     TIMESTAMPTZ,
  exit_price  DOUBLE PRECISION,
  pnl         DOUBLE PRECISION,
  pnl_pct     DOUBLE PRECISION,
  meta        JSONB
);

COMMENT ON TABLE lab.trades IS 'Хранение всех сделок (backtest + demo)';
COMMENT ON COLUMN lab.trades.run_id IS 'Идентификатор прогона стратегии';
COMMENT ON COLUMN lab.trades.strategy_id IS 'Идентификатор стратегии (например, STR-100)';
COMMENT ON COLUMN lab.trades.mode IS 'Режим торговли: backtest или demo';
COMMENT ON COLUMN lab.trades.side IS 'Направление сделки: LONG или SHORT';
COMMENT ON COLUMN lab.trades.pnl IS 'Прибыль/убыток в абсолютном значении';
COMMENT ON COLUMN lab.trades.pnl_pct IS 'Прибыль/убыток в процентах';
COMMENT ON COLUMN lab.trades.meta IS 'Дополнительные метаданные сделки';

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_trades_run_id
  ON lab.trades(run_id);

CREATE INDEX IF NOT EXISTS idx_trades_strategy_id
  ON lab.trades(strategy_id);

-- ============================================================================
-- 5. ТАБЛИЦА: lab.results - Агрегированные результаты бэктестов
-- ============================================================================
CREATE TABLE IF NOT EXISTS lab.results (
  run_id         TEXT PRIMARY KEY,
  strategy_id    TEXT NOT NULL,
  start_ts       TIMESTAMPTZ NOT NULL,
  end_ts         TIMESTAMPTZ NOT NULL,
  pnl_total      DOUBLE PRECISION NOT NULL,
  sharpe         DOUBLE PRECISION,
  sortino        DOUBLE PRECISION,
  max_dd         DOUBLE PRECISION,
  calmar         DOUBLE PRECISION,
  win_rate       DOUBLE PRECISION,
  profit_factor  DOUBLE PRECISION,
  pass_risk_gate BOOLEAN,
  meta           JSONB
);

COMMENT ON TABLE lab.results IS 'Агрегированные результаты бэктестов';
COMMENT ON COLUMN lab.results.run_id IS 'Уникальный идентификатор прогона';
COMMENT ON COLUMN lab.results.pnl_total IS 'Общая прибыль/убыток';
COMMENT ON COLUMN lab.results.sharpe IS 'Коэффициент Шарпа';
COMMENT ON COLUMN lab.results.sortino IS 'Коэффициент Сортино';
COMMENT ON COLUMN lab.results.max_dd IS 'Максимальная просадка';
COMMENT ON COLUMN lab.results.calmar IS 'Коэффициент Калмара';
COMMENT ON COLUMN lab.results.win_rate IS 'Процент прибыльных сделок';
COMMENT ON COLUMN lab.results.profit_factor IS 'Отношение прибыли к убытку';
COMMENT ON COLUMN lab.results.pass_risk_gate IS 'Прошёл ли стратегия риск-гейт';

-- ============================================================================
-- 6. ТАБЛИЦА: lab.jobs - Статусы задач TradLab
-- ============================================================================
CREATE TABLE IF NOT EXISTS lab.jobs (
  job_id      BIGSERIAL PRIMARY KEY,
  job_type    TEXT NOT NULL,  -- "collect","backtest","risk","report","demo_run"
  status      TEXT NOT NULL,  -- "pending","running","done","error"
  started_at  TIMESTAMPTZ DEFAULT now(),
  finished_at TIMESTAMPTZ,
  meta        JSONB
);

COMMENT ON TABLE lab.jobs IS 'Статусы задач TradLab';
COMMENT ON COLUMN lab.jobs.job_type IS 'Тип задачи: collect, backtest, risk, report, demo_run';
COMMENT ON COLUMN lab.jobs.status IS 'Статус задачи: pending, running, done, error';

-- ============================================================================
-- 7. VIEW: lab.features_v1 - Объединённые фичи для стратегий
-- ============================================================================
CREATE OR REPLACE VIEW lab.features_v1 AS
SELECT
  o4h.symbol,
  o4h.ts           AS ts_4h,
  o4h.open         AS open_4h,
  o4h.high         AS high_4h,
  o4h.low          AS low_4h,
  o4h.close        AS close_4h,
  o4h.volume       AS volume_4h,
  o1h.close        AS close_1h,
  NULL::DOUBLE PRECISION AS atr_14_1h,
  NULL::DOUBLE PRECISION AS sma_50_4h
FROM market.ohlcv o4h
LEFT JOIN market.ohlcv o1h
  ON o1h.symbol = o4h.symbol AND o1h.tf = '1h' AND o1h.ts = o4h.ts
WHERE o4h.tf = '4h';

COMMENT ON VIEW lab.features_v1 IS 'Объединённые фичи 4H и 1H баров для стратегий';

-- ============================================================================
-- ЗАВЕРШЕНИЕ МИГРАЦИИ
-- ============================================================================
-- Логирование применения миграции (если таблица sot_sync существует)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'eng_it' AND table_name = 'sot_sync'
  ) THEN
    INSERT INTO eng_it.sot_sync (domain_code, sync_type, status, meta)
    VALUES (
      'TL', 
      'snapshot', 
      'success', 
      jsonb_build_object(
        'migration', '20251124_003_tl_schema_l1.sql',
        'task', 'E1-B2-T1-S1',
        'description', 'TradLab L1 - схемы market и lab созданы',
        'timestamp', now()
      )
    );
  END IF;
END $$;

-- Вывод информации
DO $$
BEGIN
  RAISE NOTICE '============================================';
  RAISE NOTICE 'Миграция 20251124_003_tl_schema_l1.sql';
  RAISE NOTICE 'Задача: E1-B2-T1-S1';
  RAISE NOTICE 'Статус: ✅ УСПЕШНО ПРИМЕНЕНА';
  RAISE NOTICE '============================================';
  RAISE NOTICE 'Созданные схемы:';
  RAISE NOTICE '  ✅ market (рыночные данные)';
  RAISE NOTICE '  ✅ lab (бэктесты и результаты)';
  RAISE NOTICE 'Созданные таблицы:';
  RAISE NOTICE '  ✅ market.ohlcv';
  RAISE NOTICE '  ✅ lab.trades';
  RAISE NOTICE '  ✅ lab.results';
  RAISE NOTICE '  ✅ lab.jobs';
  RAISE NOTICE 'Созданные views:';
  RAISE NOTICE '  ✅ lab.features_v1';
  RAISE NOTICE 'Следующий шаг: E1-B2-T2 - Загрузка данных OHLCV';
  RAISE NOTICE '============================================';
END $$;
