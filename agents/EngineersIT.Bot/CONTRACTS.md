# ФОРМАЛЬНЫЕ КОНТРАКТЫ BOT V2
# Версия: 1.0.0
# Дата: 2025-10-31

## Контракт события (/events/log)
{
  \"event_id\": \"uuid4\",
  \"ts\": \"2025-10-31T10:00:00Z\", 
  \"source\": \"bot_orchestrator\",
  \"type\": \"TRIAGE_STARTED|TRIAGE_OK|DECOMP_STARTED|DECOMP_OK|PLAN_QUEUED|TASK_REFINEMENT|MONITORING_STARTED|MONITORING_COMPLETED\",
  \"trace_id\": \"uuid4\",
  \"job_id\": \"uuid4|null\",
  \"plan_id\": \"uuid4\", 
  \"parent_task_id\": \"uuid4|null\",
  \"payload\": {
    \"complexity\": 45,
    \"tags\": [\"api\", \"security\"],
    \"summary\": \"Текст описания\",
    \"tasks_count\": 3,
    \"dependencies_count\": 2
  },
  \"severity\": \"info|warning|error\",
  \"version\": \"v1\"
}

## Контракт задачи (/jobs/upsert)
{
  \"trace_id\": \"uuid4\",
  \"plan_id\": \"uuid4\", 
  \"jobs\": [
    {
      \"task_id\": \"uuid4\",
      \"parent_task_id\": \"uuid4|null\", 
      \"owner\": \"engineer_b\",
      \"type\": \"ANALYZE|IMPLEMENT|TEST|INTEGRATE|VALIDATE|DESIGN\",
      \"priority\": 80,
      \"status\": \"CREATED|QUEUED|RUNNING|PASSED|FAILED|STALLED\",
      \"idempotency_key\": \"sha256_hash\",
      \"deadline\": \"2025-10-31T12:00:00Z|null\",
      \"max_retries\": 3,
      \"payload\": {
        \"task_text\": \"Описание задачи\",
        \"candidate_patch_text\": \"текст патча|null\", 
        \"dod\": [\"Критерий 1\", \"Критерий 2\"],
        \"expected_artifacts\": [\"spec.md\", \"tests.txt\"]
      }
    }
  ]
}

## Ключи дедупликации:
- События: (trace_id, type, payload.hash) TTL 24h
- Задачи: (trace_id, plan_id, parent_task_id, type, payload.hash)

## Health-check контракт:
GET /health → { \"status\": \"healthy|degraded|unhealthy\", \"checks\": { \"db\": \"ok\", \"queue\": \"ok\" } }
GET /ready → { \"ready\": true|false, \"reason\": \"строка|null\" }
