-- A) Сводка по статусам задач в навигаторе
SELECT
  COUNT(*)                                 AS total_tasks,
  COUNT(*) FILTER (WHERE status='planned') AS planned,
  COUNT(*) FILTER (WHERE status='in_progress') AS in_progress,
  COUNT(*) FILTER (WHERE status='passed')  AS passed,
  COUNT(*) FILTER (WHERE status='failed')  AS failed
FROM eng_it.progress_navigator;

-- B) Топ-10 последних задач по обновлению
SELECT task_code, status, priority, level, module, updated_at
FROM eng_it.progress_navigator
ORDER BY updated_at DESC
LIMIT 10;

-- C) Последние 15 записей активности агентов
SELECT task_code, agent_name, status, progress_percent,
       COALESCE(evidence_uri,'') AS evidence_uri,
       started_at, finished_at,
       LEFT(COALESCE(notes,''), 120) AS notes_left120
FROM eng_it.agent_progress
ORDER BY finished_at DESC NULLS LAST, started_at DESC
LIMIT 15;

-- D) Если есть представление матрицы — текущее состояние последних 10 задач
-- (запрос не упадёт, если представления нет)
DO snapshot_self_build.sql
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.views
             WHERE table_schema='eng_it' AND table_name='v_progress_matrix') THEN
    RAISE NOTICE '--- v_progress_matrix (last 10 by priority,task_code) ---';
  END IF;
ENDsnapshot_self_build.sql;

-- Для удобства: просто отобразим строк по последним 10 task_code
WITH last_tasks AS (
  SELECT task_code
  FROM eng_it.progress_navigator
  ORDER BY updated_at DESC
  LIMIT 10
)
SELECT *
FROM eng_it.v_progress_matrix
WHERE task_code IN (SELECT task_code FROM last_tasks)
ORDER BY priority, task_code;
