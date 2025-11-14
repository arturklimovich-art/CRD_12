\copy (
  WITH ev AS (
    SELECT task_id,
           max(ts) FILTER (WHERE event_type ILIKE '%PR_MERGED%' OR event_type ILIKE '%commit_merged%') AS pr_merged_ts,
           max(ts) FILTER (WHERE event_type IN ('snapshot.done')) AS snapshot_ts,
           max(ts) FILTER (WHERE event_type IN ('test.smoke.passed','test.unit.passed')) AS tests_pass_ts,
           max(ts) FILTER (WHERE event_type IN ('plan.blocked','curator.needs_info','policy.fail')) AS blocked_ts,
           max(ts) FILTER (WHERE event_type ILIKE 'eng.code.%' OR event_type ILIKE 'test.%' OR event_type IN ('plan.plan_created')) AS work_ts
    FROM core.events
    GROUP BY task_id
  )
  SELECT * FROM ev ORDER BY task_id
) TO 'workspace/reports/STATUS_AUDIT/EVENTS_SAMPLE.csv' CSV HEADER;
