-- 1) генерим токен прямо в SQL (простая версия)
WITH latest AS (
  SELECT id
  FROM eng_it.patches
  ORDER BY created_at DESC
  LIMIT 1
),
tok AS (
  SELECT id, gen_random_uuid()::text AS token
  FROM latest
)
UPDATE eng_it.patches p
SET status = 'approved',
    approve_token = tok.token,
    curator_notes = 'approved by system-curator',
    updated_at = now()
FROM tok
WHERE p.id = tok.id;

-- 2) логируем событие
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
SELECT id,
       'curator.patch.approved',
       '{"by":"system-curator","reason":"E1-PATCH-MANUAL"}'::jsonb
FROM eng_it.patches
ORDER BY created_at DESC
LIMIT 1;

-- 3) показать патч и события
SELECT id, author, status, approve_token, created_at
FROM eng_it.patches
ORDER BY created_at DESC
LIMIT 3;

SELECT id, patch_id, event_type, ts
FROM eng_it.patch_events
ORDER BY id DESC
LIMIT 5;
