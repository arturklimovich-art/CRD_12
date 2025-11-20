import re

# Читаем файл
with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Замена 1: В SQL запросе для получения задачи - заменяем task_id на code
content = re.sub(
    r"SELECT id, task_id, title, description, status, priority",
    "SELECT id, code, title, description, status, priority",
    content
)

# Замена 2: В переменной после fetchone - task_id на code
content = re.sub(
    r'task_id = row\[1\]',
    'task_code = row[1]',
    content
)

# Замена 3: В SQL WHERE условии - id должен быть bigint, не text!
content = re.sub(
    r"WHERE id = CAST\(%s AS text\)",
    "WHERE id = %s",
    content
)

# Замена 4: В использовании task_id для отображения - используем code
content = re.sub(
    r'task_id = row\[1\]',
    'task_code = row[1]',
    content
)

# Замена 5: В сообщениях пользователю - показываем code вместо task_id
content = re.sub(
    r'\{task_id\}',
    '{task_code}',
    content
)

# Но ID остаётся для update_task_status!
# Возвращаем обратно где нужен именно id (не code)
content = re.sub(
    r'update_task_status\(task_code,',
    'update_task_status(task_id,',
    content
)

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ SQL запросы исправлены!")
print("   task_id → code (для SELECT и отображения)")
print("   CAST(%s AS text) → %s (для WHERE id)")
