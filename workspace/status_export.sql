\copy (
  SELECT task_id, status AS plan_status FROM eng_it.tasks ORDER BY task_id
) TO 'workspace/reports/STATUS_AUDIT/PLAN_STATUS_CURRENT.csv' CSV HEADER;
