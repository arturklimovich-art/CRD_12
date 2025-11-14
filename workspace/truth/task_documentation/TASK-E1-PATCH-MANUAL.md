# Task Truth Documentation: PATCH-MANUAL - Механизм ручного патча

## Task Identity
- **Code**: TASK-E1-PATCH-MANUAL
- **Title**: Внедрение механизма ручного патча (официальный apply)
- **Status**: done (VERIFIED CORRECT)
- **Verified**: 2025-11-12 12:16:53 UTC
- **Verified By**: arturklimovich-art

## Description
Реализован безопасный механизм ручного патча через отдельный Python-скрипт. 
Интеграция с Navigator DB, события, верификация через approve_token. app.py не изменён.

## Implementation Truth

### Core Components

#### 1. Standalone Script: manual_apply.py
**Location**: src/engineer_b_api/manual_apply.py
**Purpose**: Manual patch application outside main API

**Features:**
- Direct DB connection (psycopg2)
- Hardcoded PATCH_ID and APPROVE_TOKEN
- Event logging to patch_events
- SHA256 verification
- Status validation (approved only)
- Token validation

**Security**: Token verification, status check, event audit trail, SHA256 check

#### 2. API Endpoint: POST /api/patches/{patch_id}/apply
**Location**: src/engineer_b_api/routes/patches_manual.py
**Method**: POST /api/patches/{patch_id}/apply?approve_token=XXX

**Responses:** 200 (success), 404 (not found), 403 (invalid token), 409 (invalid status), 500 (error)

**Events:** eng.apply_patch.started, finished, failed

#### 3. Database Tables

**patches** (16 columns): id, task_id, author, filename, content, sha256, status, approve_token, 
created_at, applied_at, rollback_at, curator_notes, meta, generated_by, previous_version_id, target_file

**patch_events** (5 columns): id, patch_id, ts, event_type, payload

**Status Flow**: created → pending → approved → success

### What Works
- Standalone script (manual_apply.py)
- API endpoint (/api/patches/{id}/apply)
- Database integration (patches, patch_events)
- Token security
- app.py unchanged (separate files)

### Not Implemented
- Rollback mechanism
- Automatic patch discovery
- Patch version chain
- Curator workflow UI
- Patch preview/dry-run

## Database Integration
Schema: eng_it, Tables: patches (16 cols), patch_events (5 cols)

## File System Integration
Path: /app/workspace/patches_applied/ (10 patches stored, from E1-B15)

## AI Agent Knowledge
**Bot**: Patches must be approved. Use POST /api/patches/{id}/apply?approve_token=XXX
**Engineer_B**: Two ways to apply. All actions logged to patch_events
**Curator**: Review in eng_it.patches, set status=approved, add curator_notes
**Medic**: Monitor patch_events for failures, check SHA256, alert on errors

---
Generated: 2025-11-12 12:16:53 UTC
