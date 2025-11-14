-- 2025_11_navigator.sql — представления навигатора Roadmap

CREATE SCHEMA IF NOT EXISTS nav;

-- Сводка по статусам и общий прогресс
CREATE OR REPLACE VIEW nav.navigator_plan AS
SELECT
  COUNT(*)::int                                           AS total_items,
  COUNT(*) FILTER (WHERE status='planned')::int           AS planned,
  COUNT(*) FILTER (WHERE status='in_progress')::int       AS in_progress,
  COUNT(*) FILTER (WHERE status='blocked')::int           AS blocked,
  COUNT(*) FILTER (WHERE status='done')::int              AS done,
  CASE WHEN COUNT(*)=0 THEN 0.0
       ELSE ROUND(100.0 * (COUNT(*) FILTER (WHERE status='done')) / COUNT(*), 2)
  END                                                     AS progress_pct
FROM nav.roadmap_items;

-- Упорядоченный список элементов для быстрого отображения
CREATE OR REPLACE VIEW nav.navigator_items_ordered AS
SELECT item_id, parent_id, title, status, priority, owner, order_index, active_revision_id, created_at, updated_at
FROM nav.roadmap_items
ORDER BY order_index NULLS LAST, created_at;

