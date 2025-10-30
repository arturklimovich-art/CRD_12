-- Вставляем первые 5 задач из оригинальной спецификации
INSERT INTO eng_it.progress_navigator 
  (task_code, title, level, module, priority, estimated_hours, description) 
VALUES
  ('L1-T001', 'Инициализация схемы БД и базовых таблиц', 'B', 'database', 1, 2, 'Создание таблиц: progress_navigator, agent_progress, task_dependencies, system_snapshots и представлений v_progress_matrix, v_self_building_metrics. (Этот шаг уже выполнен)'),
  ('L1-T002', 'Настройка подключения к LLM API', 'B', 'infrastructure', 1, 1, 'Обеспечить, чтобы система (особенно Engineer B) могла гарантированно подключаться к API LLM (DeepSeek, Gemini).'),
  ('L1-T003', 'Создание базового манифеста AgentGraph B', 'B', 'configuration', 1, 1, 'Описать в виде конфигурационного файла (например, YAML или JSON) состав агентов: Bot, Task Manager, Engineer B, Curator, Medic.'),
  ('L1-T004', 'Реализация простого Orchestrator API', 'B', 'api', 2, 4, 'Создание базовых эндпоинтов в Task Manager для управления процессом самостроительства: /system/bootstrap/start, /system/bootstrap/progress, /system/bootstrap/rollback.'),
  ('L1-T005', 'Настройка системы версионирования', 'B', 'infrastructure', 2, 2, 'Интеграция с Git. Система должна иметь возможность коммитить свои изменения (артефакты) в репозиторий.');

-- Сразу помечаем первый шаг как выполненный (мы его только что сделали)
UPDATE eng_it.progress_navigator 
SET status = 'passed' 
WHERE task_code = 'L1-T001';

-- Также фиксируем прогресс агента (в данном случае "куратора", то есть нас)
INSERT INTO eng_it.agent_progress
  (task_code, agent_name, status, notes)
VALUES
  ('L1-T001', 'curator', 'passed', 'Схема БД успешно создана вручную под контролем Куратора.');

COMMIT;