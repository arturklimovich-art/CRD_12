# CRD12 — GENERAL PLAN (v0.2, pre‑TL1 readiness)
Updated: 2025-11-03 11:36:23Z

This is the single **source of truth**. Bot v3 reads this file (and the YAML twin), generates
expanded specs, and enforces Spec‑Binding via CI Spec‑Guard.

## Canon
- Repo (Windows): `C:\Users\Artur\Documents\CRD12\`
- Green paths: `/app/agents/`, `/app/src/engineer_b_api/`, `/app/src/bot/`, `/app/workspace/patches/`, `/app/workspace/ADR/`, `/app/workspace/snapshots/`
- Stack: Python 3.11.9, Postgres 16, Redis 7 (L2+), Docker Compose, Grafana 11, pytest 8
- DoD‑S0: smoke passed, status written to Navigator DB, clean snapshot created
- Movement: E1 → TL1 → E2 → TL2 → E3 → TL3
- Spec‑Binding: every task → `docs/TZ/SPEC_INDEX.yaml` (id/path/version/checksum)

## Sequence (before TL1)
1) E1‑06 (E1‑B6) — **Bot v2: planner** — DONE  
2) E1‑07 (E1‑B7) — **Bot v3: Roadmap/Readmap** — DONE  
3) E1‑08 (E1‑B8) — **Roadmap init** — PLANNED  
4) E1‑B9 — **Contour A (PowerShell)** — DONE  
5) E1‑08L (E1‑B11) — **Local LLM stack** — PLANNED (HIGH)  
6) E1‑09 (E1‑B12) — **Telegram two‑mode interface** — PLANNED  
7) E1‑10 (E1‑B10) — **Curator v1–v3** — PLANNED

## Stages (bird's‑eye)

### E1 — Engineers_IT (foundation)
- Bot v2/v3 (DONE), Roadmap init, Contour A (DONE), Local LLM, Telegram, Curator v1–v3.

### TL1 — Trading Lab (demo)
- Data Collector v0 (2–4 assets, ≥5y OHLCV D/H4), Strategies (STR‑000 baseline + 2–3 simple),
  Backtester v1 (WF windows), Risk‑Gate v1, Reports & Snapshots.

### E2 — Engineers_IT (quality & autonomy)
- Curator‑Gate, Knowledge Hub (pgvector), Scheduler/Queues, Telemetry & Reports, Security policies,
  Integration Contracts v2, Self‑healing v1.

### TL2 — Trading Lab (rich data & paper)
- M‑series strategies, WF+CV batches, Paper executor with kill‑switch, Digests (daily/weekly).

### E3 — Engineers_IT (industrial)
- Blue/Green + Canary, HA & Degradation, End‑to‑end Audit, Cost/Budget guardrails,
  Risk‑Gates v3, Multi‑tenant & A/B experiments.

### TL3 — Trading Lab (live)
- Small live loop with kill‑switch, Portfolio allocator (CVaR budgeting), A/B on live share,
  Compliance & Audit pack.

## Blocks summary
- E1‑B6..B12 and E1‑B10 fully defined in YAML twin; TL1/TL2/TL3 blocks also specified in YAML with tasks, DoD, and metrics.
- CI Spec‑Guard validates Roadmap schema & Spec‑Binding and runs smoke tests per DoD.
