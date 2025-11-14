-- Insert new task for PatchService refactoring
INSERT INTO eng_it.roadmap_tasks (
    code,
    title,
    block_code,
    block_title,
    block_status,
    status,
    kind,
    priority,
    description,
    created_at,
    updated_at
) VALUES (
    'E1-B16-IMPL-PATCHSERVICE',
    'Рефакторинг app.py: выделение PatchService для централизации логики применения патчей',
    'E1-B16',
    'PatchManager Integration',
    'in_progress',
    'planned',
    'refactoring',
    80,
    'Выделить логику применения патчей из app.py в отдельный сервис PatchService для устранения дублирования и улучшения архитектуры. Удалить дублирующую функцию _apply_code_changes, использовать единый механизм через PatchManager.',
    NOW(),
    NOW()
);

-- Verify task creation
SELECT code, title, status, priority FROM eng_it.roadmap_tasks 
WHERE code = 'E1-B16-IMPL-PATCHSERVICE';