UPDATE eng_it.roadmap_tasks 
SET status = 'in_progress', updated_at = NOW() 
WHERE code = 'E1-B16-IMPL-PATCHSERVICE';

-- Подтверждение обновления
SELECT code, title, status, updated_at FROM eng_it.roadmap_tasks 
WHERE code = 'E1-B16-IMPL-PATCHSERVICE';
