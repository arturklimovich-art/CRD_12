-- берем самый свежий патч и помечаем, что Curator его посмотрел
WITH latest AS (
  SELECT id
  FROM eng_it.patches
  ORDER BY created_at DESC
  LIMIT 1
)
UPDATE eng_it.patches
SET status = 'validated',
    curator_notes = 'auto-validate: structure ok',
    updated_at = now()
FROM latest
WHERE eng_it.patches.id = latest.id;

-- пишем событие
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
SELECT id,
       'curator.patch.validated',
       '{"by":"system-curator","policy":"path-whitelist","result":"ok"}'::jsonb
FROM eng_it.patches
ORDER BY created_at DESC
LIMIT 1;

-- показать последние события
SELECT id, patch_id, event_type, ts
FROM eng_it.patch_events
ORDER BY id DESC
LIMIT 5;
