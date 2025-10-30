-- A) Статус задачи в навигаторе
SELECT task_code, status AS overall_status, priority, level, module, estimated_hours, actual_hours, updated_at
FROM eng_it.progress_navigator
WHERE task_code = 'SB-HEALTH-001';

-- B) Прогресс агентов (орchestrator/curator/coder/engineer_b), последние записи
SELECT task_code, agent_name, status, progress_percent, evidence_uri, started_at, finished_at, notes
FROM eng_it.agent_progress
WHERE task_code = 'SB-HEALTH-001'
ORDER BY finished_at DESC NULLS LAST, started_at DESC;

-- C) Строка из матрицы (если view создан)
SELECT *
FROM eng_it.v_progress_matrix
WHERE task_code = 'SB-HEALTH-001';
