-- ============================================================================
-- Migration: Fix lab.features_v1 - Add SMA and ATR calculations
-- Date: 2025-11-25
-- Description: Replace NULL indicators with real calculations
-- ============================================================================

CREATE OR REPLACE VIEW lab.features_v1 AS
WITH 
-- Расчёт SMA_50 для 4H
sma_4h AS (
  SELECT
    symbol,
    ts,
    AVG(close) OVER (
      PARTITION BY symbol 
      ORDER BY ts 
      ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ) AS sma_50
  FROM market.ohlcv
  WHERE tf = '4h'
),
-- Расчёт ATR_14 для 1H
atr_1h AS (
  SELECT
    symbol,
    ts,
    AVG(high - low) OVER (
      PARTITION BY symbol 
      ORDER BY ts 
      ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS atr_14
  FROM market.ohlcv
  WHERE tf = '1h'
),
-- Расчёт средного объёма за 20 периодов (4H)
avg_vol_4h AS (
  SELECT
    symbol,
    ts,
    AVG(volume) OVER (
      PARTITION BY symbol 
      ORDER BY ts 
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS avg_volume_20
  FROM market.ohlcv
  WHERE tf = '4h'
)
SELECT
  o4h.symbol,
  o4h.ts           AS ts_4h,
  o4h.open         AS open_4h,
  o4h.high         AS high_4h,
  o4h.low          AS low_4h,
  o4h.close        AS close_4h,
  o4h.volume       AS volume_4h,
  o1h.close        AS close_1h,
  atr.atr_14       AS atr_14_1h,
  sma.sma_50       AS sma_50_4h,
  vol.avg_volume_20 AS avg_volume_20
FROM market.ohlcv o4h
LEFT JOIN market.ohlcv o1h
  ON o1h.symbol = o4h.symbol 
  AND o1h.tf = '1h' 
  AND o1h.ts = o4h.ts
LEFT JOIN sma_4h sma
  ON sma.symbol = o4h.symbol 
  AND sma.ts = o4h.ts
LEFT JOIN atr_1h atr
  ON atr.symbol = o4h.symbol 
  AND atr.ts = o4h.ts
LEFT JOIN avg_vol_4h vol
  ON vol.symbol = o4h.symbol 
  AND vol.ts = o4h.ts
WHERE o4h.tf = '4h'
ORDER BY o4h.ts;

COMMENT ON VIEW lab.features_v1 IS 'Features with calculated SMA_50, ATR_14, AVG_VOLUME_20';

-- ============================================================================
-- End of migration
-- ============================================================================
