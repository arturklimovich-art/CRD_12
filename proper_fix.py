with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем функцию run_roadmap_command и исправляем SQL
old_sql = '''SELECT id, task_id, title, description, status, priority
                     FROM eng_it.roadmap_tasks
                     WHERE status = 'planned'
                     ORDER BY priority DESC
                     LIMIT 1'''

new_sql = '''SELECT id, code, title, description, status, priority
                     FROM eng_it.roadmap_tasks
                     WHERE status = 'planned'
                     ORDER BY priority DESC
                     LIMIT 1'''

content = content.replace(old_sql, new_sql)

# Исправляем распаковку результата
content = content.replace(
    'task_id = row[1]',
    'task_code = row[1]  # code колонка вместо task_id'
)

# Исправляем функцию update_task_status - id это bigint, не text!
content = content.replace(
    "WHERE id = CAST(%s AS text)",
    "WHERE id = %s  # id is bigint, not text"
)

# Исправляем отображение в сообщениях
content = content.replace(
    'f"📝 ID: `{task_id}`"',
    'f"📝 ID: `{task_id}`\\n📋 Code: `{task_code}`"'
)

content = content.replace(
    'f"Task done! ID: {task_id}"',
    'f"Task done! ID: {task_id} ({task_code})"'
)

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправления применены!")
