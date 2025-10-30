-- 1. Сбрасываем L1-T005 (которая 'failed') обратно в 'planned'
UPDATE eng_it.progress_navigator
SET status = 'planned'
WHERE task_code = 'L1-T005';

-- Очищаем прогресс агентов по ней
DELETE FROM eng_it.agent_progress WHERE task_code = 'L1-T005';

-- 2. Загружаем Фазу 1.2: Базовые возможности
INSERT INTO eng_it.progress_navigator 
  (task_code, title, level, module, priority, estimated_hours) 
VALUES
  ('L1-T006', 'Реализация пайплайна выполнения задач', 'B', 'orchestration', 2, 6),
  ('L1-T007', 'Создание системы логгирования и аудита', 'B', 'monitoring', 2, 3),
  ('L1-T008', 'Интеграция с Git для хранения артефактов', 'B', 'integration', 2, 3),
  ('L1-T009', 'Базовые проверки кода (линтеры)', 'B', 'quality', 3, 4),
  ('L1-T010', 'Система отката на предыдущие версии', 'B', 'reliability', 2, 3);

COMMIT;