#!/usr/bin/env python3
import re

print("Читаем bot_integrated.py...")
with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Всего строк: {len(lines)}")

# Найдём функцию run_roadmap_command
in_function = False
function_start = -1

for i, line in enumerate(lines):
    if 'def run_roadmap_command' in line:
        in_function = True
        function_start = i
        print(f"Найдена функция run_roadmap_command на строке {i+1}")
    
    # Исправление 1: SQL SELECT
    if in_function and 'SELECT id, task_id' in line and 'roadmap_tasks' in line:
        print(f"Строка {i+1}: Заменяем task_id на code в SELECT")
        lines[i] = line.replace('task_id', 'code')
    
    # Исправление 2: Переменная после fetchone
    if in_function and 'task_id = row[1]' in line:
        print(f"Строка {i+1}: Заменяем task_id = row[1] на task_code = row[1]")
        lines[i] = line.replace('task_id = row[1]', 'task_code = row[1]  # code column')
    
    # Исправление 3: Использование в строках
    if in_function and '{task_id}' in line and 'task_code' not in line:
        # Не заменяем в update_task_status(task_id, ...) - там нужен id!
        if 'update_task_status' not in line:
            print(f"Строка {i+1}: Заменяем {{task_id}} на {{task_code}}")
            lines[i] = line.replace('{task_id}', '{task_code}')

# Найдём функцию update_task_status
for i, line in enumerate(lines):
    if 'def update_task_status' in line:
        print(f"Найдена функция update_task_status на строке {i+1}")
    
    # Исправление 4: WHERE id = CAST(%s AS text) → WHERE id = %s
    if 'WHERE id = CAST(%s AS text)' in line:
        print(f"Строка {i+1}: Убираем CAST для id (bigint)")
        lines[i] = line.replace('WHERE id = CAST(%s AS text)', 'WHERE id = %s')

print("Записываем изменения...")
with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Исправления применены!")
print("")
print("Проверка:")
import subprocess
result = subprocess.run(['grep', '-n', 'SELECT id, code', '/app/bot_integrated.py'], 
                       capture_output=True, text=True)
if result.stdout:
    print("✅ Найден SELECT id, code:", result.stdout[:200])
else:
    print("❌ SELECT id, code не найден!")

result = subprocess.run(['grep', '-n', 'task_code = row', '/app/bot_integrated.py'], 
                       capture_output=True, text=True)
if result.stdout:
    print("✅ Найден task_code = row:", result.stdout[:200])
else:
    print("❌ task_code = row не найден!")
