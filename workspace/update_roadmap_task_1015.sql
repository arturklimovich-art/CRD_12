-- workspace/update_roadmap_task_1015.sql
-- Обновление задачи 1015 (E1-B11 LLM Events Logging) в roadmap_tasks
-- Дата: 2025-11-17 17:03:12 UTC
-- Статус: done (логирование событий llm.* реализовано)

UPDATE eng_it.roadmap_tasks
SET
  status = 'done',
  completed_at = '2025-11-17 17:03:12+00'::timestamptz,
  description = '✅ Логирование событий llm.* в core.events реализовано и работает. Функция send_system_event() в events.py записывает события в БД. llm_router.py логирует llm.request, llm.response, llm.inference.metrics. Тестирование пройдено. Интеграция Ollama — отдельная задача.',
  steps = '[
    {\"code\": \"E1-B11-S1\", \"title\": \"Реализация events.py для логирования в core.events\", \"status\": \"done\", \"done\": true},
    {\"code\": \"E1-B11-S2\", \"title\": \"Добавление логирования llm.* в llm_router.py\", \"status\": \"done\", \"done\": true},
    {\"code\": \"E1-B11-S3\", \"title\": \"Тестирование событий llm.*\", \"status\": \"done\", \"done\": true}
  ]'::jsonb,
  mechanisms = '[
    {\"kind\": \"file\", \"ref\": \"src/app/engineer_b_api/events.py\", \"description\": \"Функция логирования событий в core.events\"},
    {\"kind\": \"file\", \"ref\": \"src/app/engineer_b_api/llm_router.py\", \"description\": \"LLM-роутер с логированием событий\"},
    {\"kind\": \"db_table\", \"ref\": \"core.events\", \"description\": \"Таблица событий (append-only log)\"},
    {\"kind\": \"view\", \"ref\": \"core.v_llm_events\", \"description\": \"View для фильтрации событий llm.*\"}
  ]'::jsonb,
  artifacts = '[
    {\"kind\": \"code\", \"ref\": \"commit:6694e62\", \"description\": \"feat(llm): add event logging to Engineer_API_B\", \"created_at\": \"2025-11-17T16:59:00Z\"},
    {\"kind\": \"log\", \"ref\": \"core.events:llm.*\", \"description\": \"События llm.test, llm.provider.switched в БД\", \"created_at\": \"2025-11-17T16:57:54Z\"}
  ]'::jsonb,
  updated_at = NOW()
WHERE id = 1015;

-- Обновление eng_it.tasks
UPDATE eng_it.tasks
SET
  status = 'done',
  progress_notes = '✅ Логирование событий llm.* реализовано в Engineer_API_B (events.py + llm_router.py). События llm.request, llm.response, llm.inference.metrics, llm.provider.switched работают и фиксируются в core.events. Интеграция Ollama (L0-L3) — отдельная задача в будущем.',
  updated_at = NOW()
WHERE id = '1015';
