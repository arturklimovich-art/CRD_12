#!/usr/bin/env python3

# Читаем файл
with open('/app/bot_integrated.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Старая (неправильная) функция
old_function = '''def get_next_planned_task() -> Optional[dict]:
    """Получает следующую planned задачу из Roadmap"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, priority, created_at, telegram_chat_id
                FROM eng_it.tasks
                WHERE status = 'planned'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            task = cur.fetchone()
        conn.close()
        return dict(task) if task else None
    except Exception as e:
        logger.error(f"Failed to get next task: {e}")
        return None'''

# Новая (правильная) функция
new_function = '''def get_next_planned_task() -> Optional[dict]:
    """Получает следующую planned задачу из Roadmap"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, code, title, description, status, priority
                FROM eng_it.roadmap_tasks
                WHERE status = 'planned'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            task = cur.fetchone()
        conn.close()
        return dict(task) if task else None
    except Exception as e:
        logger.error(f"Failed to get next task: {e}")
        return None'''

# Замена функции
if old_function in content:
    content = content.replace(old_function, new_function)
    print("✅ Функция заменена целиком!")
else:
    # Попробуем заменить только критические части
    print("⚠️ Полная замена не удалась, пробуем частичную...")
    
    # Заменяем таблицу
    content = content.replace(
        'FROM eng_it.tasks',
        'FROM eng_it.roadmap_tasks'
    )
    
    # Заменяем SELECT
    content = content.replace(
        'SELECT id, title, priority, created_at, telegram_chat_id',
        'SELECT id, code, title, description, status, priority'
    )
    
    print("✅ Частичные замены применены!")

# Записываем обратно
with open('/app/bot_integrated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n📋 Проверка результата:")
import subprocess

# Показываем исправленную функцию
result = subprocess.run(['sed', '-n', '108,128p', '/app/bot_integrated.py'], 
                       capture_output=True, text=True)
print(result.stdout)

# Проверяем что roadmap_tasks теперь используется
result = subprocess.run(['grep', '-n', 'FROM eng_it.roadmap_tasks', '/app/bot_integrated.py'], 
                       capture_output=True, text=True)
if result.stdout:
    print("\n✅ ПРАВИЛЬНАЯ ТАБЛИЦА НАЙДЕНА:")
    print(result.stdout)
else:
    print("\n❌ roadmap_tasks не найдена!")

# Проверяем что колонка code добавлена
result = subprocess.run(['grep', '-n', 'SELECT id, code', '/app/bot_integrated.py'], 
                       capture_output=True, text=True)
if result.stdout:
    print("\n✅ КОЛОНКА code НАЙДЕНА:")
    print(result.stdout)
else:
    print("\n❌ Колонка code не найдена!")
