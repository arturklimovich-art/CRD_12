-- workspace/update_roadmap_task_1001_r4_done.sql
-- Mark R4 step as done for task 1001
UPDATE eng_it.roadmap_tasks
SET
  steps = jsonb_set(
    jsonb_set(steps, '{3,status}', '"done"'),
    '{3,done}', 'true'
  ),
  updated_at = NOW()
WHERE id = 1001;
