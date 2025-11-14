-- Шаблон событий применения патча для E1-PATCH-MANUAL

WITH last_patch AS (
    SELECT id
    FROM eng_it.patches
    WHERE status = 'approved'
    ORDER BY created_at DESC
    LIMIT 1
)
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
SELECT id,
       'eng.apply_patch.started',
       '{"by":"manual-simulator","reason":"pre-code-impl"}'::jsonb
FROM last_patch;

WITH last_patch AS (
    SELECT id
    FROM eng_it.patches
    WHERE status = 'approved'
    ORDER BY created_at DESC
    LIMIT 1
)
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
SELECT id,
       'eng.apply_patch.finished',
       '{"result":"success","smoke":"not-run"}'::jsonb
FROM last_patch;

-- пример отката (можно комментировать при обычном сценарии)
WITH last_patch AS (
    SELECT id
    FROM eng_it.patches
    WHERE status = 'approved'
    ORDER BY created_at DESC
    LIMIT 1
)
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
SELECT id,
       'eng.apply_patch.rolled_back',
       '{"result":"rollback","reason":"simulated"}'::jsonb
FROM last_patch;

-- показать последние события
SELECT id, patch_id, event_type, ts
FROM eng_it.patch_events
ORDER BY id DESC
LIMIT 10;
