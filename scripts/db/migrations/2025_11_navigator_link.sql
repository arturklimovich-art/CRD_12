-- 2025_11_navigator_link.sql — связь задач Engineer_B ↔ Roadmap

CREATE OR REPLACE VIEW nav.navigator_tasks_link AS
SELECT
  j.job_id,
  j.task_type,
  j.status        AS job_status,
  j.created_at,
  j.finished_at,
  j.meta->>'tz_id'          AS tz_id,
  j.meta->>'correlation_id' AS correlation_id,
  j.meta->>'item_id'        AS item_id,
  i.title,
  i.status                  AS roadmap_status,
  i.priority,
  i.owner,
  i.order_index
FROM core.jobs j
LEFT JOIN nav.roadmap_items i
  ON i.item_id::text = j.meta->>'item_id'
WHERE j.task_type = 'engineer_tz'
ORDER BY j.created_at DESC;

