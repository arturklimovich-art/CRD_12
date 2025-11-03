# Handshake v0.2 (PowerShell Console A ↔ Engineers_IT B ↔ Journal/Policies C)
- Input: TZ (8‑line template or .md/.yaml path)
- Events: ps.patch.created, ps.patch.request_apply, eng.apply_patch.{accepted,smoke_passed,committed,rolled_back}
- Idempotency: idem_key per operation
- Approvals: Curator approve_token for risk>threshold
- Environments: dev / stage / prod
- White‑path: only via A→B; direct edits blocked or journaled as manual.change
