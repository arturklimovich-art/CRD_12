#!/usr/bin/env python3

with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправление: заменяем result.get("status") на result.get("engineer_status")
changes = 0

# Замена 1: Чтение статуса из result
if 'result.get("status"' in content:
    content = content.replace(
        'result.get("status"',
        'result.get("engineer_status"'
    )
    changes += 1
    print("✅ Заменено: result.get('status') → result.get('engineer_status')")

# Проверка что generated_code тоже правильный
if 'result.get("generated_code"' not in content:
    print("⚠️ Внимание: result.get('generated_code') не найден!")
else:
    print("✅ result.get('generated_code') найден - OK")

with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

if changes > 0:
    print(f"\n✅ Применено изменений: {changes}")
else:
    print("\n⚠️ Изменений не найдено - возможно уже исправлено")

# Показываем исправленный код
import subprocess
print("\n📋 Проверка исправлений:")
result = subprocess.run(
    ['grep', '-n', 'engineer_status', '/app/bot_integrated.py'],
    capture_output=True, text=True
)
if result.stdout:
    print("✅ engineer_status найден:")
    for line in result.stdout.split('\n')[:5]:
        print(f"  {line}")
else:
    print("❌ engineer_status не найден!")
