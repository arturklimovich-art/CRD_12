-- Загружаем Фазу 2.1: Интеллектуальная маршрутизация
INSERT INTO eng_it.progress_navigator 
  (task_code, title, level, module, priority, estimated_hours) 
VALUES
  ('L2-T001', 'Система оценки сложности задач', 'A', 'intelligence', 2, 6),
  ('L2-T002', 'Адаптивная маршрутизация к агентам', 'A', 'orchestration', 2, 5),
  ('L2-T003', 'Shadow-тестирование новых возможностей', 'A', 'testing', 3, 4),
  ('L2-T004', 'Canary-развертывание изменений', 'A', 'deployment', 3, 4),
  ('L2-T005', 'Автоматический анализ метрик качества', 'A', 'analytics', 3, 5);
      
COMMIT;
