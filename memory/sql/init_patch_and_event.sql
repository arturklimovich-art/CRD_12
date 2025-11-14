-- 1) создаём служебный патч
WITH ins AS (
  INSERT INTO eng_it.patches (author, filename, content, sha256, status, meta)
  VALUES (
    'system',
    'bootstrap.patch',
    '\x',
    'BOOTSTRAP_SHA256',
    'submitted',
    '{"source":"bootstrap","task":"E1-PATCH-MANUAL"}'
  )
  RETURNING id
)
-- 2) сразу пишем событие к нему
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
SELECT id,
       'plan.patch.pipeline_created',
       '{"reason":"init E1-PATCH-MANUAL","by":"system"}'::jsonb
FROM ins;

-- 3) показать, что получилось
SELECT id, patch_id, event_type, ts
FROM eng_it.patch_events
ORDER BY id DESC
LIMIT 5;
