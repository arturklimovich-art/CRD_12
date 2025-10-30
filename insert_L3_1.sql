-- Загружаем Фазу 3.1: Самоисцеление и оптимизация
INSERT INTO eng_it.progress_navigator
  (task_code, title, level, module, priority, estimated_hours)
VALUES
  ('L3-T001', 'Система предсказания сбоев', 'S', 'reliability', 2, 8),
  ('L3-T002', 'Автоматическое восстановление при ошибках', 'S', 'reliability', 2, 7),
  ('L3-T003', 'Предиктивная маршрутизация задач', 'S', 'intelligence', 3, 6),
  ('L3-T004', 'Автоматическая оптимизация пайплайнов', 'S', 'optimization', 3, 6),
  ('L3-T005', 'Система самообучения на ошибках', 'S', 'intelligence', 3, 8);

COMMIT;
