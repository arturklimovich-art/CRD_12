-- СРОЧНО: Добавляем основную задачу оптимизации с приоритетом 0 (самый высокий)
INSERT INTO eng_it.progress_navigator
  (task_code, title, description, level, module, priority, estimated_hours)
VALUES
  ('OPTIM-001-URGENT', 'СРОЧНАЯ оптимизация цикла поиска', 'Заменить постоянный 30-секундный цикл на умный sleep: 30сек при задачах, 300сек когда задач нет', 'B', 'performance', 0, 1);

COMMIT;
