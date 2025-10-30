-- Загружаем Фазу 2.2: Дебаты и коллективный разум
INSERT INTO eng_it.progress_navigator 
  (task_code, title, level, module, priority, estimated_hours) 
VALUES
  ('L2-T006', 'Debate Orchestrator сервис', 'A', 'intelligence', 2, 8),
  ('L2-T007', 'Механизм арбитража между агентами', 'A', 'intelligence', 3, 6),
  ('L2-T008', 'Система голосования и консенсуса', 'A', 'intelligence', 3, 5),
  ('L2-T009', 'Адаптивное прекращение дебатов', 'A', 'optimization', 3, 4),
  ('L2-T010', 'Переход с уровня B на уровень A', 'A', 'evolution', 1, 3);
      
COMMIT;
