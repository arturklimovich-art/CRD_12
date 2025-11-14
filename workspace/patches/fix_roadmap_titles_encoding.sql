-- Fix encoding for roadmap_tasks titles
-- Date: 2025-11-12 12:31:15 UTC
-- Issue: Titles display as ??????? due to encoding mismatch

BEGIN;

-- Update titles with correct UTF-8 encoding
UPDATE eng_it.roadmap_tasks SET title = 'E1-B7 Bot v3: интеграция Roadmap/Readmap' WHERE code = 'TASK-1002';
UPDATE eng_it.roadmap_tasks SET title = 'E1-B9 PowerShell скрипты' WHERE code = 'TASK-1003';
UPDATE eng_it.roadmap_tasks SET title = 'E1-L1 События/ADR/Базовая история' WHERE code = 'TASK-1005';
UPDATE eng_it.roadmap_tasks SET title = 'E1-L2 Navigator DB (углубленная проекция)' WHERE code = 'TASK-1006';
UPDATE eng_it.roadmap_tasks SET title = 'E1-L4 Куча-стейт и патч-файлы (при rebuild)' WHERE code = 'TASK-1008';
UPDATE eng_it.roadmap_tasks SET title = 'E1-L5 Прогресс-навигатор (мультиагентный)' WHERE code = 'TASK-1009';

-- Verify updates
SELECT code, title, status FROM eng_it.roadmap_tasks WHERE code IN (
    'TASK-1002', 'TASK-1003', 'TASK-1005', 'TASK-1006', 
    'TASK-1008', 'TASK-1009', 'TASK-1018', 'TASK-E1-PATCH-MANUAL'
) ORDER BY code;

COMMIT;
