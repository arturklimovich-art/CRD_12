-- workspace/update_roadmap_task_1001_r5_done.sql
-- Mark R5 step as done for task 1001
UPDATE eng_it.roadmap_tasks
SET
  steps = jsonb_set(
    jsonb_set(steps, '{4,status}', '"done"'),
    '{4,done}', 'true'
  ),
  updated_at = NOW()
WHERE id = 1001;
