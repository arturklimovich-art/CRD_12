#!/usr/bin/env python3
# Патч для добавления Roadmap router в app.py

import sys
import re

# Читаем app.py
with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем, не добавлен ли уже
if 'roadmap_router' in content:
    print('✓ Roadmap router уже в app.py')
    sys.exit(0)

# Найти место после создания FastAPI app
app_pattern = r'(app\s*=\s*FastAPI\([^)]+\))'
match = re.search(app_pattern, content, re.DOTALL)

if not match:
    print('❌ Не найдено создание FastAPI app')
    sys.exit(1)

# Вставляем код подключения router
insert_code = '''

# ===== ROADMAP MODULE =====
try:
    from routes.roadmap import router as roadmap_router
    app.include_router(roadmap_router)
    print("✅ Roadmap router подключён")
except Exception as e:
    print(f"⚠️ Roadmap router недоступен: {e}")
'''

# Вставляем после создания app
new_content = content.replace(match.group(0), match.group(0) + insert_code)

# Сохраняем
with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✅ Патч применён успешно')
