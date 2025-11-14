INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
SELECT id,
       'plan.patch.pipeline_created',
       '{"reason":"init E1-PATCH-MANUAL","by":"system"}'::jsonb
FROM eng_it.patches
ORDER BY created_at ASC
LIMIT 1;

SELECT id, patch_id, event_type, ts
FROM eng_it.patch_events
ORDER BY id DESC
LIMIT 5;
