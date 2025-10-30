-- Тестовая задача для проверки цикла self-build
INSERT INTO eng_it.progress_navigator
  (task_code, title, level, module, priority, status, estimated_hours)
VALUES
  ('SB-HEALTH-001', 'Проверка цикла self-build (минимальная)', 'B', 'orchestration', 1, 'planned', 1)
ON CONFLICT (task_code) DO UPDATE
SET status = EXCLUDED.status,
    updated_at = now();
