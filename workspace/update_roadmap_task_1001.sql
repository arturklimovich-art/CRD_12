-- workspace/update_roadmap_task_1001.sql
-- Update task 1001 (E1-B6 Bot v2: Intelligent Planner)
-- Date: 2025-11-17 17:22:00 UTC
-- Status: in_progress (planning complete, implementation pending)

UPDATE eng_it.roadmap_tasks
SET
  description = 'Bot v2 becomes project manager. Manages ROADMAP.yaml <-> ROADMAP.md (single source of truth), detects DRIFT, creates revisions, generates TZ for Engineer_B from E1-TL3 tasks, maintains JOURNAL (events, statuses, commitSHA), integrates with Navigator (progress) and Kurator (gates). Commands: Roadmap-Load, Roadmap-Sync, Roadmap-Edit, Roadmap-Approve, Roadmap-GenerateTZ, Roadmap-UpdateStatus.',
  steps = '[
    {"code": "E1-B6-R1", "title": "R1: Init and validate ROADMAP (Roadmap-Load)", "status": "planned", "done": false},
    {"code": "E1-B6-R2", "title": "R2: Sync YAML <-> MD and DRIFT detector (Roadmap-Sync)", "status": "planned", "done": false},
    {"code": "E1-B6-R3", "title": "R3: Roadmap revisions (Roadmap-Edit, Roadmap-Approve)", "status": "planned", "done": false},
    {"code": "E1-B6-R4", "title": "R4: Generate TZ from ROADMAP tasks (Roadmap-GenerateTZ)", "status": "planned", "done": false},
    {"code": "E1-B6-R5", "title": "R5: Statuses and JOURNAL (Roadmap-UpdateStatus)", "status": "planned", "done": false},
    {"code": "E1-B6-R6", "title": "R6: Navigator and Kurator integration (progress, gates, events)", "status": "planned", "done": false}
  ]'::jsonb,
  mechanisms = '[
    {"kind": "file", "ref": "ROADMAP/ROADMAP.yaml", "description": "Single source of truth (structured plan E1-TL3)"},
    {"kind": "file", "ref": "ROADMAP/ROADMAP.md", "description": "Human-readable plan version"},
    {"kind": "directory", "ref": "workspace/roadmap/revisions/", "description": "Append-only Roadmap revisions"},
    {"kind": "directory", "ref": "JOURNAL/", "description": "Event log (events, statuses, incidents)"},
    {"kind": "command", "ref": "Roadmap-Load", "description": "Load and validate ROADMAP"},
    {"kind": "command", "ref": "Roadmap-Sync", "description": "DRIFT detector (YAML <-> MD)"},
    {"kind": "command", "ref": "Roadmap-Edit", "description": "Create draft revision"},
    {"kind": "command", "ref": "Roadmap-Approve", "description": "Approve revision (activate)"},
    {"kind": "command", "ref": "Roadmap-GenerateTZ", "description": "Generate TZ for Engineer_B from E*/TL* task"},
    {"kind": "command", "ref": "Roadmap-UpdateStatus", "description": "Update task status + JOURNAL"},
    {"kind": "integration", "ref": "Navigator", "description": "Display progress (stage/block/%)"},
    {"kind": "integration", "ref": "Kurator", "description": "Gate for revisions and TZ (approve/reject)"}
  ]'::jsonb,
  tz_ref = 'TZ Bot v2: R1-R6 blocks, commands, ROADMAP.yaml, JOURNAL. See full spec in task description.',
  updated_at = NOW()
WHERE id = 1001;
