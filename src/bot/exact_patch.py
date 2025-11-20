#!/usr/bin/env python3
import re

with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Сохраняем оригинал для сравнения
original = content

# Исправление 1: В get_next_planned_task() - SELECT query
# Заменяем task_id на code в SELECT
content = re.sub(
    r'(SELECT\s+id,\s+)task_id(,\s+title.*?FROM\s+eng_it\.roadmap_tasks)',
    r'\1code\2',
    content,
    flags=re.IGNORECASE | re.DOTALL
)

# Исправление 2: В get_next_planned_task() - после fetchone
# Добавляем task_code = row[1] если его нет
if 'task_code = row[1]' not in content and 'get_next_planned_task' in content:
    # Ищем возврат словаря в get_next_planned_task
    content = re.sub(
        r'(return\s+{\s*"id":\s*row\[0\],\s*)"task_id":\s*row\[1\]',
        r'\1"code": row[1]',
        content
    )

# Исправление 3: В run_roadmap_command - добавляем task_code
# После task_id = task["id"] добавляем task_code = task.get("code", "N/A")
content = re.sub(
    r'(task_id\s*=\s*task\["id"\]\s*\n\s*task_title\s*=\s*task\["title"\])',
    r'\1\n    task_code = task.get("code", "N/A")  # Added: code column',
    content
)

# Исправление 4: WHERE id = CAST(%s AS text) → WHERE id = %s
content = content.replace(
    'WHERE id = CAST(%s AS text)',
    'WHERE id = %s  # id is bigint'
)

# Проверяем что изменилось
if content != original:
    with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Исправления применены!")
    
    # Показываем что изменилось
    import subprocess
    
    print("\n📋 Проверка изменений:")
    
    # Проверка 1: code в SELECT
    result = subprocess.run(['grep', '-n', 'SELECT.*code.*FROM eng_it.roadmap_tasks', '/app/bot_integrated.py'], 
                           capture_output=True, text=True)
    if result.stdout:
        print("✅ SQL с 'code' найден:")
        print(result.stdout[:300])
    else:
        print("❌ SQL с 'code' не найден")
    
    # Проверка 2: task_code в run_roadmap_command
    result = subprocess.run(['grep', '-n', 'task_code = task.get', '/app/bot_integrated.py'], 
                           capture_output=True, text=True)
    if result.stdout:
        print("✅ task_code = task.get найден:")
        print(result.stdout)
    else:
        print("❌ task_code = task.get не найден")
    
    # Проверка 3: "code" в return словаре
    result = subprocess.run(['grep', '-n', '"code": row', '/app/bot_integrated.py'], 
                           capture_output=True, text=True)
    if result.stdout:
        print("✅ 'code': row найден в словаре:")
        print(result.stdout)
    else:
        print("⚠️ 'code': row не найден (может быть другой формат)")
        
else:
    print("❌ Ничего не изменилось! Проверьте паттерны.")
    print("\nПоиск текущих паттернов:")
    import subprocess
    
    result = subprocess.run(['grep', '-A5', 'def get_next_planned_task', '/app/bot_integrated.py'], 
                           capture_output=True, text=True)
    print("get_next_planned_task():")
    print(result.stdout[:500])
