-- Загружаем Фазу 3.2: Мета-управление и эволюция
INSERT INTO eng_it.progress_navigator
  (task_code, title, level, module, priority, estimated_hours)
VALUES
  ('L3-T006', 'Автоматическое создание улучшений', 'S', 'evolution', 2, 10),
  ('L3-T007', 'Система оценки эффективности изменений', 'S', 'analytics', 3, 5),
  ('L3-T008', 'Генерация новых возможностей системы', 'S', 'innovation', 3, 8),
  ('L3-T009', 'Полная автономия самостроительства', 'S', 'evolution', 1, 12),
  ('L3-T010', 'Документация и передача знаний', 'S', 'documentation', 4, 6);

COMMIT;
