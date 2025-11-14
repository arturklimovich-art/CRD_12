-- Insert new task for PatchService refactoring with correct schema
INSERT INTO eng_it.roadmap_tasks (
    id,
    code,
    title,
    status,
    kind,
    priority,
    description,
    tz_ref,
    block_id,
    created_at,
    updated_at
) VALUES (
    2001,  -- ID задачи
    'E1-B16-IMPL-PATCHSERVICE',
    'Рефакторинг app.py: выделение PatchService для централизации логики применения патчей',
    'planned',  -- planned | in_progress | done | failed | blocked | removed
    'task',     -- task | subtask | epic | milestone
    80,         -- приоритет
    'Выделить логику применения патчей из app.py в отдельный сервис PatchService для устранения дублирования и улучшения архитектуры. Удалить дублирующую функцию _apply_code_changes, использовать единый механизм через PatchManager.',
    'docs/TZ/E1-B16-IMPL-PATCHSERVICE.md',  -- ссылка на техническое задание
    16,         -- block_id для E1-B16
    NOW(),
    NOW()
);

-- Verify task creation
SELECT id, code, title, status, priority FROM eng_it.roadmap_tasks 
WHERE code = 'E1-B16-IMPL-PATCHSERVICE';