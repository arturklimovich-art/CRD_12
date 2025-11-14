-- TRUTH_SCHEMA.sql (Plan A)
create extension if not exists pgcrypto;

create table if not exists eng_it.truth_revisions (
  rev_id        uuid primary key default gen_random_uuid(),
  file_path     text not null,
  sha256        text not null,
  commit_sha    text,
  committed_at  timestamptz default now(),
  actor         text,
  is_active     boolean not null default false
);
create unique index if not exists uq_eng_it_truth_active on eng_it.truth_revisions (is_active) where is_active;

create table if not exists eng_it.evidence_artifacts (
  id            bigserial primary key,
  kind          text not null,               -- 'fs' | 'sql' | 'http' | 'event'
  path_or_query text not null,
  result_hash   text,
  created_at    timestamptz default now()
);

create table if not exists eng_it.task_verdicts (
  id            bigserial primary key,
  task_title    text not null,
  rev_id        uuid not null references eng_it.truth_revisions(rev_id) on delete cascade,
  status        text not null check (status in ('planned','in_progress','done')),
  evidence_id   bigint references eng_it.evidence_artifacts(id),
  verdict_ts    timestamptz default now()
);

create or replace view eng_it.v_truth_matrix as
select
  t.title,
  t.status                           as navigator_status,
  tv.status                          as verified_status,
  (tv.evidence_id is not null)       as has_evidence,
  tv.verdict_ts,
  tr.sha256,
  tr.file_path
from eng_it.tasks t
left join lateral (
  select tv1.*
  from eng_it.task_verdicts tv1
  where tv1.task_title = t.title
  order by tv1.verdict_ts desc
  limit 1
) tv on true
left join eng_it.truth_revisions tr on tr.rev_id = tv.rev_id;
