-- СРОЧНО: Задача с КОНКРЕТНЫМ кодом исправления
INSERT INTO eng_it.progress_navigator
  (task_code, title, description, level, module, priority, estimated_hours)
VALUES
  ('OPTIM-001-FIX', 'РЕАЛЬНОЕ исправление цикла поиска', 'Заменить код в task_manager.py: заменить текущий цикл на оптимизированную версию с short_sleep=30 и long_sleep=300', 'B', 'performance', 0, 1);

COMMIT;
