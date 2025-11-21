#!/usr/bin/env python3

with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ищем функцию update_task_status
import re

# Исправление: task_id это bigint (число), не text!
# Убираем все попытки привести к text или добавляем CAST к bigint

# Вариант 1: Если используется %s без CAST
content = re.sub(
    r"(UPDATE eng_it\.roadmap_tasks.*?WHERE id = )%s",
    r"\1CAST(%s AS bigint)",
    content,
    flags=re.DOTALL
)

# Вариант 2: Убираем CAST AS text если есть
content = content.replace("CAST(%s AS text)", "CAST(%s AS bigint)")

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ update_task_status исправлена!")

# Проверка
import subprocess
result = subprocess.run(['grep', '-A5', 'def update_task_status', '/app/bot_integrated.py'], 
                       capture_output=True, text=True)
print("\n📋 Функция update_task_status:")
print(result.stdout[:500])
