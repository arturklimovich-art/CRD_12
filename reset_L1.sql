-- Сбрасываем ВЕСЬ УРОВЕНЬ 1 обратно в 'planned'
UPDATE eng_it.progress_navigator
SET status = 'planned'
WHERE level = 'B' AND task_code != 'L1-T001'; -- (L1-T001 - это создание БД, оно УЖЕ сделано)

-- Очищаем ВЕСЬ прогресс агентов (кроме L1-T001)
DELETE FROM eng_it.agent_progress 
WHERE task_code != 'L1-T001';

COMMIT;