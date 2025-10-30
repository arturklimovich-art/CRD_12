-- Восстанавливаем задачу OPTIM-001-FIX с статусом planned
UPDATE eng_it.progress_navigator 
SET status = 'planned', 
    description = 'СРОЧНО: Исправить цикл в task_manager.py - заменить на оптимизированную версию с short_sleep=30 и long_sleep=300'
WHERE task_code = 'OPTIM-001-FIX';

-- Если записи нет - создаем заново
INSERT INTO eng_it.progress_navigator 
  (task_code, title, description, level, module, priority, estimated_hours, status)
SELECT 
  'OPTIM-001-FIX', 
  'РЕАЛЬНОЕ исправление цикла поиска', 
  'СРОЧНО: Исправить цикл в task_manager.py - заменить на оптимизированную версию с short_sleep=30 и long_sleep=300',
  'B', 
  'performance', 
  0, 
  1,
  'planned'
WHERE NOT EXISTS (
  SELECT 1 FROM eng_it.progress_navigator WHERE task_code = 'OPTIM-001-FIX'
);

COMMIT;
