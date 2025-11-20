-- workspace/update_roadmap_task_1001_r1_done.sql
-- Mark R1 step as done for task 1001
UPDATE eng_it.roadmap_tasks
SET
  steps = jsonb_set(
    jsonb_set(steps, '{0,status}', '"done"'),
    '{0,done}', 'true'
  ),
  updated_at = NOW()
WHERE id = 1001;
