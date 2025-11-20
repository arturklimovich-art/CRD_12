#!/usr/bin/env python3

# Читаем файл
with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Ищем функцию get_next_planned_task()...")

# Ищем строки функции (примерно 108-128)
changed = False
for i in range(len(lines)):
    line = lines[i]
    
    # Исправление 1: В SELECT заменяем task_id на code
    if 'SELECT' in line and 'task_id' in line and i >= 108 and i <= 128:
        print(f"Строка {i+1}: Найден SELECT с task_id")
        print(f"  Было: {line.strip()}")
        lines[i] = line.replace('task_id', 'code')
        print(f"  Стало: {lines[i].strip()}")
        changed = True
    
    # Исправление 2: В return словаре заменяем "task_id" на "code"
    if '"task_id":' in line and i >= 108 and i <= 128:
        print(f"Строка {i+1}: Найден 'task_id' в словаре")
        print(f"  Было: {line.strip()}")
        lines[i] = line.replace('"task_id":', '"code":')
        print(f"  Стало: {lines[i].strip()}")
        changed = True

if changed:
    # Записываем обратно
    with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("\n✅ SQL запрос исправлен!")
else:
    print("\n❌ Изменения не найдены. Показываем текущую функцию:")
    for i in range(108, 128):
        if i < len(lines):
            print(f"{i+1}: {lines[i]}", end='')

# Проверка результата
print("\n📋 Проверка исправлений:")
import subprocess

result = subprocess.run(['sed', '-n', '108,128p', '/app/bot_integrated.py'], 
                       capture_output=True, text=True)
print(result.stdout)
