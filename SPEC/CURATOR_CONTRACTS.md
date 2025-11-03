# Curator Contracts & Data Model
Statuses: pending, in_progress, resolved, unresolved, rejected, needs_info, parked
Job types: SPEC_CREATE, SPEC_REFINE, TASK_BUILD, TASK_REWORK, PATCH_APPLY, TEST_RUN
Events: TASK_FAILED, CURATOR_TAKEN, CURATOR_RCA_DONE, SPEC_REPAIRED, TEST_STUB_ATTACHED, REWORK_ENQUEUED, POLICY_OK, POLICY_FAIL, WHITE_PATH_VIOLATION, SLA_BREACH_IMMINENT, SLA_BREACH
REST: POST /curator/triage|refine|requeue, GET /curator/status/{task_id}
