import sys

# Читаем исходный файл
with open('/app/jobs_ultra_simple.py', 'rb') as f:
    content = f.read()

# Удаляем BOM если он есть
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]
    print("✅ BOM символ удален")
else:
    print("ℹ️ BOM символ не найден")

# Записываем обратно без BOM
with open('/app/jobs_ultra_simple.py', 'wb') as f:
    f.write(content)

print("✅ Файл перезаписан без BOM")
